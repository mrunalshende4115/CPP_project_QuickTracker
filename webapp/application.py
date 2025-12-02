import sys
import os
import boto3
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Flask, render_template, request
from quicktrack4115.checkin import check_in
from quicktrack4115.checkout import check_out
from quicktrack_utils.db import update_status
from quicktrack_utils.db import delete_vehicle
from quicktrack_utils.db import is_vehicle_registered
from quicktrack_utils.alerts import send_sns_alert
from flask import redirect, url_for, flash
from quicktrack_utils.s3_utils import upload_vehicle_docs, get_presigned_url
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from quicktrack_utils.user import get_user, User
from quicktrack_utils.vehicle import register_vehicle, get_vehicles_by_warehouse
from quicktrack_utils.logger import log_event, send_audit_message
from datetime import datetime


application = Flask(__name__)
application.secret_key = 'your-secret-key'

# Configure Flask-Login for user authentication

login_manager = LoginManager()
login_manager.init_app(application)
login_manager.login_view = 'login' 

# Load user from DynamoDB when Flask-Login needs it

@login_manager.user_loader
def load_user(username):
    return get_user(username)

@application.route('/register_user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        warehouse_id = request.form['warehouse_id']
        session = boto3.Session(region_name='us-east-1')
        dynamodb = session.resource('dynamodb')
        user_table = dynamodb.Table('QuickTrackUsers')
        user_table.put_item(Item={
            "username": username,
            "password": password,
            "warehouse_id": warehouse_id
        })
        flash("User registered successfully")
        return redirect(url_for('login'))
    return render_template('register_user.html')

@application.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print("Login form submitted:", username, password)
        
        session = boto3.Session(region_name='us-east-1')
        dynamodb = session.resource('dynamodb')
        user_table = dynamodb.Table('QuickTrackUsers')

        try:
            response = user_table.get_item(Key={"username": username})
            item = response.get("Item")
            print("Login attempt:", username)
            print("Fetched item:", item)
        except Exception as e:
            print("DynamoDB error:", e)
            flash("AWS error during login")
            return redirect(url_for('login'))

        if item:
            print("Stored password:", item["password"])
            if item["password"] == password:
                user = User(
                    username=item["username"],
                    warehouse_id=item["warehouse_id"],
                    role=item.get("role", "user")  
                )
                login_user(user)
                print(" Login successful for:", username)
                return redirect(url_for('index'))
            else:
                print(" Password mismatch for:", username)
        else:
            print(" No user found for:", username)

        flash("Invalid credentials")
        return redirect(url_for('login'))

    return render_template('login.html')


@application.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('login'))

#VEHICLE MANAGEMENT

@application.route('/')
@login_required
def index():
    vehicles = get_vehicles_by_warehouse(current_user.warehouse_id)
    return render_template('index.html', vehicles=vehicles)

@application.route('/register', methods=['POST'])
@login_required
def register():
    vehicle_id = request.form['vehicle_id']
    driver_name = request.form['driver_name']
    vehicle_type = request.form['vehicle_type']
    warehouse_id = current_user.warehouse_id  

    # Prevent duplicate registration

    if is_vehicle_registered(vehicle_id, warehouse_id):
        flash(f" Vehicle {vehicle_id} is already registered.")
        return redirect(url_for('index'))

    # Upload registration and insurance docs to S3

    reg_file = request.files['registration_doc']
    ins_file = request.files['insurance_doc']
    reg_url, ins_url = upload_vehicle_docs(vehicle_id, reg_file, ins_file)

    # Save vehicle record in DB

    success = register_vehicle(vehicle_id, driver_name, vehicle_type, reg_url, ins_url, warehouse_id)

    if success:
        flash(f" Vehicle {vehicle_id} registered successfully.")
    else:
        flash(f" Registration failed due to unknown error.")

    return redirect(url_for('index'))
    
@application.route('/checkin', methods=['POST'])
@login_required
def checkin():
    vehicle_id = request.form['vehicle_id']
    warehouse_id = current_user.warehouse_id
    location = "Warehouse"
    status = "available"
    username = current_user.username
    data = check_in(vehicle_id, location)
    success = update_status(vehicle_id, data['status'], data['location'], warehouse_id)

    if not success:
        flash(f" Check-in failed: Vehicle {vehicle_id} is not currently in use.")
    else:
        send_sns_alert(vehicle_id, "check-in", location, warehouse_id, username)
        flash(f" Vehicle {vehicle_id} checked in to Warehouse successfully.")

    return redirect(url_for('index'))

@application.route('/checkout', methods=['POST'])
@login_required
def checkout():
    vehicle_id = request.form['vehicle_id']
    location = request.form['location']
    warehouse_id = current_user.warehouse_id
    username = current_user.username

    # Ensure vehicle is registered before checkout

    if not is_vehicle_registered(vehicle_id, warehouse_id):
        send_sns_alert(vehicle_id, "check-out", "failed", warehouse_id, username)
        flash(f" Check-out failed: Vehicle {vehicle_id} is not registered in warehouse {warehouse_id}.")
        return render_template('vehicle.html', vehicle_id=vehicle_id, action="Check-Out Failed")

    data = check_out(vehicle_id, location)
    success = update_status(vehicle_id, data['status'], data['location'], warehouse_id)

    if not success:
        flash(f" Check-out failed: Invalid state transition or warehouse mismatch.")
        return render_template('vehicle.html', vehicle_id=vehicle_id, action="Check-Out Failed")

    send_sns_alert(vehicle_id, "check-out", location, warehouse_id, username)
    flash(f"Vehicle {vehicle_id} checked out from {location}.")
    return render_template('vehicle.html', vehicle_id=vehicle_id, action="Checked Out")

# ashboard route
@application.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    print("Dashboard accessed by:", current_user.username)
    print("Warehouse ID:", current_user.warehouse_id)

    try:
        vehicles = get_vehicles_by_warehouse(current_user.warehouse_id)
        print("Fetched vehicles:", vehicles)
        
        for v in vehicles:
           v['registration_doc_url'] = get_presigned_url(v['vehicle_id'], 'registration')
           v['insurance_doc_url'] = get_presigned_url(v['vehicle_id'], 'insurance')
     
    except Exception as e:
        print("Error fetching vehicles:", e)
        flash("Error loading dashboard data.")
        vehicles = []

    return render_template('dashboard.html', vehicles=vehicles, current_year=datetime.now().year)
    
@application.route('/delete', methods=['POST'])
@login_required
def delete():
    vehicle_id = request.form['vehicle_id']
    warehouse_id = current_user.warehouse_id
    username = current_user.username

    success = delete_vehicle(vehicle_id, warehouse_id)

    if success:
        send_sns_alert(vehicle_id, "deleted", "N/A", warehouse_id, username)
        send_audit_message(vehicle_id, "delete", "success", warehouse_id, username)
        log_event(f"Vehicle {vehicle_id} deleted by {username} from warehouse {warehouse_id}")
        flash(f"Vehicle {vehicle_id} deleted and alert sent.")
    else:
        send_audit_message(vehicle_id, "delete", "failed", warehouse_id, username)
        log_event(f"Failed to delete vehicle {vehicle_id} by {username} from warehouse {warehouse_id}")
        flash(f"Failed to delete vehicle {vehicle_id}.")

    return redirect(url_for('index'))


if __name__ == '__main__':
   port = int(os.environ.get("PORT", 5000))
   application.run(host="0.0.0.0", port=port)

