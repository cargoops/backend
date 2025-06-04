import json
from boto3.dynamodb.conditions import Key
from common.utils import packages_table, respond

def lambda_handler(event, context):
    auth = event['requestContext'].get('authorizer', {})
    eid  = auth.get('employee_id')

    if auth.get('role') == 'tq_employee':
        # only your own orders
        resp = packages_table.query(
            IndexName='TqEmployeeIndex',
            KeyConditionExpression=Key('tq_employee_id').eq(eid)
        )
        items = resp.get('Items', [])
    elif auth.get('role') == 'admin':
        items = packages_table.scan().get('Items', [])
    else:
        return respond(403, {'message':'Forbidden'})

    return respond(200, {'data': items})
