import json
from boto3.dynamodb.conditions import Key
from common.utils import storing_table, respond

def lambda_handler(event, context):
    auth = event['requestContext'].get('authorizer', {})
    eid  = auth.get('employee_id')

    if auth.get('role') == 'receiver':
        # only your own orders
        resp = storing_table.query(
            IndexName='ReceiverIndex',
            KeyConditionExpression=Key('receiver_id').eq(eid)
        )
        items = resp.get('Items', [])
    elif auth.get('role') == 'admin':
        items = storing_table.scan().get('Items', [])
    else:
        return respond(403, {'message':'Forbidden'})

    return respond(200, {'data': items})
