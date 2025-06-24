import json
from boto3.dynamodb.conditions import Key
from common.utils import packages_table, respond

def lambda_handler(event, context):
    params = event.get('queryStringParameters') or {}
    role = params.get('role')
    employee_id = params.get('employee_id')
    if role == 'tq_employee':
        resp = packages_table.query(
            IndexName='TqEmployeeIndex',
            KeyConditionExpression=Key('tq_employee_id').eq(employee_id)
        )
        items = resp.get('Items', [])
    elif role == 'admin':
        items = packages_table.scan().get('Items', [])
    else:
        return respond(403, {'message':'Forbidden'})
    return respond(200, {'data': items})
