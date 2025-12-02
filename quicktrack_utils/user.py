from flask_login import UserMixin
import boto3

#usermixin used for authentication

class User(UserMixin):
    def __init__(self, username, warehouse_id, role=None):
        self.id = username
        self.username = username
        self.warehouse_id = warehouse_id
        self.role = role 


def get_user(username):
#Looks for records where primary key is username.
    session = boto3.Session(region_name='us-east-1')
    dynamodb = session.resource('dynamodb')
    user_table = dynamodb.Table('QuickTrackUsers')

    try:
        response = user_table.get_item(Key={"username": username})
        item = response.get("Item")
        if item:
            return User(username=item["username"], warehouse_id=item["warehouse_id"])
    except Exception as e:
        print("DynamoDB error in get_user:", e)
    return None