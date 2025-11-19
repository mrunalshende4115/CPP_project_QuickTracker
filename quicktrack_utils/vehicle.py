import json
import boto3
from boto3.dynamodb.conditions import Attr
from datetime import datetime

# ✅ Helper to get a fresh DynamoDB table reference
def get_vehicle_table():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    return dynamodb.Table('QuickTrackVehicles')  # ✅ Correct table name

# ✅ Register a single vehicle
def register_vehicle(vehicle_id, driver_name, vehicle_type, registration_doc_url, insurance_doc_url, warehouse_id):
    vehicle_table = get_vehicle_table()
    item = {
        'vehicle_id': vehicle_id,
        'driver_name': driver_name,
        'vehicle_type': vehicle_type,
        'warehouse_id': warehouse_id,
        'status': 'registered',
        'location': 'N/A',
        'registration_doc_url': registration_doc_url,
        'insurance_doc_url': insurance_doc_url,
        'timestamp': datetime.utcnow().isoformat()
    }
    try:
        vehicle_table.put_item(Item=item)
        print(f"✅ Registered vehicle: {vehicle_id}")
        return True
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        return False


# ✅ Register multiple vehicles from a JSON file
def batch_register(filepath, warehouse_id):
    with open(filepath, 'r') as f:
        vehicles = json.load(f)
    for v in vehicles:
        register_vehicle(
            v['vehicle_id'],
            v['driver_name'],
            v['vehicle_type'],
            v.get('registration_doc_url', ''),
            v.get('insurance_doc_url', ''),
            warehouse_id
        )

# ✅ Fetch vehicles by warehouse
def get_vehicles_by_warehouse(warehouse_id):
    vehicle_table = get_vehicle_table()
    response = vehicle_table.scan(
        FilterExpression=Attr("warehouse_id").eq(warehouse_id)
    )
    return response.get('Items', [])
    
# ✅ Delete a vehicle by ID and warehouse
def delete_vehicle(vehicle_id, warehouse_id):
    vehicle_table = get_vehicle_table()
    try:
        response = vehicle_table.delete_item(
            Key={
                'vehicle_id': vehicle_id,
                'warehouse_id': warehouse_id
            }
        )
        return True
    except Exception as e:
        print(f"❌ Delete failed for {vehicle_id}: {e}")
        return False
