import json
from boto3.dynamodb.conditions import Key
from common.utils import storing_table, respond

def lambda_handler(event, context):
    print("Received event:", event)
    params = event.get('queryStringParameters') or {}
    eid  = params.get('employee_id')
    role = params.get('role')
    print("Employee ID:", eid)
    print("Auth role:", role)
    if role == 'receiver':
        print("Processing receiver role request")
        resp = storing_table.query(
            IndexName='ReceiverIndex',
            KeyConditionExpression=Key('receiver_id').eq(eid)
        )
        items = resp.get('Items', [])
        print("Found items for receiver:", len(items))
    elif role == 'admin':
        print("Processing admin role request")
        items = storing_table.scan().get('Items', [])
        print("Found items for admin:", len(items))
    else:
        print("Forbidden access attempt")
        return respond(403, {'message':'Forbidden'})
    print("Returning response with items")
    return respond(200, {'data': items})
