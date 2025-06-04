import json
from boto3.dynamodb.conditions import Key
from common.utils import storing_table, respond

def lambda_handler(event, context):
    print("Received event:", event)
    auth = event['requestContext'].get('authorizer', {})
    eid  = auth.get('employee_id')
    print("Employee ID:", eid)
    print("Auth role:", auth.get('role'))

    if auth.get('role') == 'receiver':
        print("Processing receiver role request")
        # only your own orders
        resp = storing_table.query(
            IndexName='ReceiverIndex',
            KeyConditionExpression=Key('receiver_id').eq(eid)
        )
        items = resp.get('Items', [])
        print("Found items for receiver:", len(items))
    elif auth.get('role') == 'admin':
        print("Processing admin role request")
        items = storing_table.scan().get('Items', [])
        print("Found items for admin:", len(items))
    else:
        print("Forbidden access attempt")
        return respond(403, {'message':'Forbidden'})

    print("Returning response with items")
    return respond(200, {'data': items})
