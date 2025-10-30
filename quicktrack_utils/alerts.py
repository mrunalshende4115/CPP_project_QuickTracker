import boto3
sns = boto3.client('sns')
TOPIC_ARN = 'arn:aws:sns:us-east-1:772676455545:QuickTrackAlerts'

def send_sns_alert(vehicle_id, action, status="success"):
    message = f"Vehicle ID: {vehicle_id}\nAction: {action}\nStatus: {status}"
    subject = f"QuickTrack Alert: {action} - {status.upper()}"
    
    sns.publish(
        TopicArn=TOPIC_ARN,
        Message=message,
        Subject=subject
    )
