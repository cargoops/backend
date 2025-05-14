import json, datetime
from boto3.dynamodb.conditions import Key
from common.utils import storing_table, packages_table, respond

def lambda_handler(event, context):
    auth = event['requestContext']['authorizer']
    if auth['role'] != 'receiver':
        return respond(403, {'message':'Forbidden'})

    try:
        b = json.loads(event['body'])
        sid = b['storing_order_id']
        inv = b['invoice_number']
        bill= b['bill_of_entry_id']
        awb = b['airway_bill_number']
        qty = b['quantity']
    except Exception:
        return respond(400, {'message':'Invalid input'})

    # fetch order
    r = storing_table.get_item(Key={'storing_order_id': sid})
    order = r.get('Item')
    if not order:
        return respond(404, {'message':'Order not found'})

    # check mismatches
    mismatches = []
    if order.get('invoice_number')    != inv:  mismatches.append('invoice_number')
    if order.get('bill_of_entry_id')  != bill: mismatches.append('bill_of_entry_id')
    if order.get('airway_bill_number')!= awb:  mismatches.append('airway_bill_number')
    if order.get('package_quantity')  != qty:  mismatches.append('package_quantity')

    if mismatches:
        detail = f"Mismatches: {','.join(mismatches)}"
        # mark FAILED
        storing_table.update_item(
            Key={'storing_order_id': sid},
            UpdateExpression="SET #s=:s, discrepancy_detail=:d",
            ExpressionAttributeNames={'#s':'status'},
            ExpressionAttributeValues={':s':'INSPECTION-FAILED', ':d': detail}
        )
        # update all packages
        pkgs = packages_table.query(
            IndexName='StoringOrderIndex',
            KeyConditionExpression=Key('storing_order_id').eq(sid)
        ).get('Items', [])
        for p in pkgs:
            packages_table.update_item(
                Key={'package_id': p['package_id']},
                UpdateExpression="SET #s=:s",
                ExpressionAttributeNames={'#s':'status'},
                ExpressionAttributeValues={':s':'INSPECTION-FAILED'}
            )
        return respond(400, {'message':'Inspection failed','discrepancy_detail': detail})

    # mark RECEIVED
    now = datetime.datetime.utcnow().isoformat()
    storing_table.update_item(
        Key={'storing_order_id': sid},
        UpdateExpression="SET #s=:s, received_date=:r",
        ExpressionAttributeNames={'#s':'status'},
        ExpressionAttributeValues={':s':'RECEIVED', ':r': now}
    )
    # update packages → READY-FOR-TQ
    pkgs = packages_table.query(
        IndexName='StoringOrderIndex',
        KeyConditionExpression=Key('storing_order_id').eq(sid)
    ).get('Items', [])
    for p in pkgs:
        packages_table.update_item(
            Key={'package_id': p['package_id']},
            UpdateExpression="SET #s=:s",
            ExpressionAttributeNames={'#s':'status'},
            ExpressionAttributeValues={':s':'READY-FOR-TQ'}
        )
    return respond(200, {'message':'Order received'})
