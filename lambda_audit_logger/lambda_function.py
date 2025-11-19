import json
import boto3
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('AlertAuditLog')

def lambda_handler(event, context):
    for record in event['Records']:
        alert = json.loads(record['body'])
        alert['alert_id'] = str(uuid.uuid4())
        alert['timestamp'] = datetime.utcnow().isoformat()
        table.put_item(Item=alert)
        print(f"Logged alert: {alert}")
