from botocore.exceptions import ClientError
import boto3
from boto3.dynamodb.conditions import Attr
from datetime import datetime
from quicktrack_utils.vehicle import get_vehicle_table

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('QuickTrackVehicles')

# ✅ Insert vehicle with warehouse_id
def put_vehicle(item):
    try:
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(vehicle_id)'
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return False
        else:
            raise

# ✅ Check if vehicle exists in user's warehouse
def is_vehicle_registered(vehicle_id, warehouse_id):
    response = table.get_item(Key={'vehicle_id': vehicle_id})
    item = response.get('Item')
    return item and item.get('warehouse_id') == warehouse_id

# ✅ Register vehicle with warehouse_id
def register_vehicle(vehicle_id, driver_name, vehicle_type, reg_url, ins_url, warehouse_id):
    try:
        table.put_item(
            Item={
                'vehicle_id': vehicle_id,
                'driver_name': driver_name,
                'vehicle_type': vehicle_type,
                'warehouse_id': warehouse_id,
                'status': 'registered',
                'location': 'N/A',
                'registration_doc_url': reg_url,  # ✅ updated
                'insurance_doc_url': ins_url,
                'timestamp': datetime.utcnow().isoformat()
            },
            ConditionExpression='attribute_not_exists(vehicle_id)'
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return False
        else:
            raise

# ✅ Update status only if vehicle belongs to user's warehouse

def update_status(vehicle_id, status, location, warehouse_id):
    table = get_vehicle_table()

    try:
        response = table.get_item(Key={'vehicle_id': vehicle_id})
        item = response.get('Item')

        if not item or item.get('warehouse_id') != warehouse_id:
            print(f"❌ Update rejected: vehicle not found or warehouse mismatch")
            return False

        if status == 'available' and location == 'Warehouse':
            if item.get('status') != 'in_use':
                print(f"❌ Invalid transition: {item.get('status')} → {status}")
                return False

        table.update_item(
            Key={'vehicle_id': vehicle_id},
            UpdateExpression="SET #s = :s, #loc = :l, #u = :u",
            ExpressionAttributeNames={
                '#s': 'status',
                '#loc': 'location',
                '#u': 'updated_at'
            },
            ExpressionAttributeValues={
                ':s': status,
                ':l': location,
                ':u': datetime.utcnow().isoformat()
            }
        )
        print(f"✅ Updated status for {vehicle_id} to {status} at {location} in warehouse {warehouse_id}")
        return True

    except Exception as e:
        print(f"❌ Failed to update status: {e}")
        return False


# ✅ Get all vehicles for a specific warehouse
def get_vehicles_by_warehouse(warehouse_id):
    table = get_vehicle_table()
    response = table.scan(
        FilterExpression=Attr('warehouse_id').eq(warehouse_id)
    )
    vehicles = response.get('Items', [])
    return vehicles  # ✅ Each item should include the URLs

# ✅ Delete vehicle only if it belongs to user's warehouse
def delete_vehicle(vehicle_id, warehouse_id):
    try:
        response = table.get_item(Key={'vehicle_id': vehicle_id})
        item = response.get('Item')
        if not item or item.get('warehouse_id') != warehouse_id:
            print(f"❌ Vehicle {vehicle_id} not found or unauthorized.")
            return False

        table.delete_item(Key={'vehicle_id': vehicle_id})
        print(f"✅ Vehicle {vehicle_id} deleted successfully.")
        return True

    except ClientError as e:
        print(f"⚠️ Error deleting vehicle {vehicle_id}: {e}")
        return False