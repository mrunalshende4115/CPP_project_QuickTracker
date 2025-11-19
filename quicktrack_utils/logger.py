import logging
import watchtower
import boto3
import json
from datetime import datetime


logger = logging.getLogger("quicktrack")
logger.setLevel(logging.INFO)
logger.addHandler(watchtower.CloudWatchLogHandler(log_group="QuickTrackLogs"))

def log_event(message):
    logger.info(message)
    
def send_audit_message(vehicle_id, action, status, warehouse_id, user):
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = "https://sqs.us-east-1.amazonaws.com/772676455545/QuickTrackAlertAuditQueue"

    message = {
        "vehicle_id": vehicle_id,
        "action": action,
        "status": status,
        "warehouse_id": warehouse_id,
        "performed_by": user,
        "timestamp": datetime.utcnow().isoformat()
    }

    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message)
    )
