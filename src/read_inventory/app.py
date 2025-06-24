import json
from common.utils import inventory_table, respond

def lambda_handler(event, context):
    print("Received event:", event)
    params = event.get('queryStringParameters') or {}
    role = params.get('role')
    employee_id = params.get('employee_id')
    print("Role:", role)
    if role != 'admin':
        print("Forbidden: not admin")
        return respond(403, {'message': 'Forbidden'})
    print("Scanning Inventory table...")
    items = inventory_table.scan().get('Items', [])
    print(f"Found {len(items)} inventory items.")
    return respond(200, {'data': items})
