import json
from quicktrack_utils.db import put_vehicle

def register_vehicle(vehicle_id, driver_name, vehicle_type):
    item = {
        'vehicle_id': vehicle_id,
        'driver_name': driver_name,
        'vehicle_type': vehicle_type,
        'status': 'registered',
        'location': 'N/A'
    }
    put_vehicle(item)

def batch_register(filepath):
    with open(filepath, 'r') as f:
        vehicles = json.load(f)
    for v in vehicles:
        register_vehicle(v['vehicle_id'], v['driver_name'], v['vehicle_type'])