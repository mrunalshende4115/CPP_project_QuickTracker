import boto3
import json
from datetime import datetime

sns_client = boto3.client('sns')
sqs_client = boto3.client('sqs')

VEHICLE_TOPIC_ARN = "arn:aws:sns:us-east-1:150302467911:QuickTrackAlerts"
VEHICLE_DELETION_TOPIC_ARN = "arn:aws:sns:us-east-1:150302467911:QuickTrackVehicleDeletion"
ALERT_AUDIT_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/150302467911/QuickTrackAlertAuditQueue"

def send_sns_alert(vehicle_id, action, location, warehouse_id, performed_by):
    # Always send audit log to SQS
    audit_payload = {
        "vehicle_id": vehicle_id,
        "action": action,
        "location": location,
        "warehouse_id": warehouse_id,
        "performed_by": performed_by,
        "timestamp": datetime.utcnow().isoformat()
    }

    sqs_client.send_message(
        QueueUrl=ALERT_AUDIT_QUEUE_URL,
        MessageBody=json.dumps(audit_payload)
    )

    # Only send email if action is deletion
    if action == "deleted":
        subject = "Vehicle Deletion Alert"
        message = f"Vehicle {vehicle_id} was deleted from the registry."

        sns_client.publish(
            TopicArn=VEHICLE_DELETION_TOPIC_ARN,
            Message=message,
            Subject=subject
        )