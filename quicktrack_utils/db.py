from botocore.exceptions import ClientError
import boto3
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('QuickTrackVehicles')

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

    
def is_vehicle_registered(vehicle_id):
    response = table.get_item(Key={'vehicle_id': vehicle_id})
    return 'Item' in response
    
def register_vehicle(vehicle_id, driver_name, vehicle_type):
    try:
        table.put_item(
            Item={
                'vehicle_id': vehicle_id,
                'driver_name': driver_name,
                'vehicle_type': vehicle_type,
                'status': 'registered',
                'location': 'N/A'
            },
            ConditionExpression='attribute_not_exists(vehicle_id)'  # ✅ Prevent overwrite
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return False  # Already registered
        else:
            raise
  # Other error

def update_status(vehicle_id, status, location):
    table.update_item(
        Key={'vehicle_id': vehicle_id},
        UpdateExpression="SET #s = :s, #loc = :l",
        ExpressionAttributeNames={
            '#s': 'status',
            '#loc': 'location'  # alias for reserved word
        },
        ExpressionAttributeValues={
            ':s': status,
            ':l': location
        }
    )
    
def get_all_vehicles():
    response = table.scan()
    return response.get('Items', [])
    
def delete_vehicle(vehicle_id):
    table.delete_item(Key={'vehicle_id': vehicle_id})