import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Flask, render_template, request
from quicktrack4115.checkin import check_in
from quicktrack4115.checkout import check_out
from quicktrack_utils.vehicle import register_vehicle
from quicktrack_utils.db import update_status, get_all_vehicles
from quicktrack_utils.db import delete_vehicle
from quicktrack_utils.db import is_vehicle_registered
from quicktrack_utils.alerts import send_sns_alert


app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    vehicle_id = request.form['vehicle_id']
    driver_name = request.form['driver_name']
    vehicle_type = request.form['vehicle_type']

    success = register_vehicle(vehicle_id, driver_name, vehicle_type)

    if not success:
        return render_template('vehicle.html', vehicle_id=vehicle_id, action="Registration Failed: Vehicle Already Registered")

    return render_template('vehicle.html', vehicle_id=vehicle_id, action="Registered")
@app.route('/checkin', methods=['POST'])
def checkin():
    vehicle_id = request.form['vehicle_id']
    location = request.form['location']

    if not is_vehicle_registered(vehicle_id):
        send_sns_alert(vehicle_id, "check-in", "failed")
        return render_template('vehicle.html', vehicle_id=vehicle_id, action="Check-In Failed: Vehicle Not Registered")

    data = check_in(vehicle_id, location)
    update_status(**data)
    send_sns_alert(vehicle_id, "check-in", "success")
    return render_template('vehicle.html', vehicle_id=vehicle_id, action="Checked In")

@app.route('/checkout', methods=['POST'])
def checkout():
    vehicle_id = request.form['vehicle_id']
    location = request.form['location']

    if not is_vehicle_registered(vehicle_id):
        send_sns_alert(vehicle_id, "check-out", "failed")
        return render_template('vehicle.html', vehicle_id=vehicle_id, action="Check-Out Failed: Vehicle Not Registered")

    data = check_out(vehicle_id, location)
    update_status(**data)
    send_sns_alert(vehicle_id, "check-out", "success")
    return render_template('vehicle.html', vehicle_id=vehicle_id, action="Checked Out")


# ✅ NEW: Dashboard route
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    vehicles = get_all_vehicles()
    return render_template('dashboard.html', vehicles=vehicles)

@app.route('/delete', methods=['POST'])
def delete():
    vehicle_id = request.form['vehicle_id']
    delete_vehicle(vehicle_id)
    return render_template('vehicle.html', vehicle_id=vehicle_id, action="Deleted")



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)