import json
from common.utils import inventory_table, respond

def lambda_handler(event, context):
    print("Received event:", event)
    auth = event['requestContext'].get('authorizer', {})
    print("Auth:", auth)
    if auth.get('role') != 'admin':
        print("Forbidden: not admin")
        return respond(403, {'message': 'Forbidden'})

    print("Scanning Inventory table...")
    items = inventory_table.scan().get('Items', [])
    print(f"Found {len(items)} inventory items.")
    return respond(200, {'data': items})
