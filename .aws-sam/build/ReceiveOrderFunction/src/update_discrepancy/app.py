import json
from common.utils import storing_table, respond

def lambda_handler(event, context):
    auth = event['requestContext']['authorizer']
    if auth['role'] != 'receiver':
        return respond(403, {'message':'Forbidden'})

    try:
        b = json.loads(event['body'])
        sid = b['storing_order_id']
        detail = b['discrepancy_detail']
    except Exception:
        return respond(400, {'message':'Invalid input'})

    r = storing_table.get_item(Key={'storing_order_id': sid})
    order = r.get('Item')
    if not order:
        return respond(404, {'message':'Order not found'})
    if order.get('status') != 'INSPECTION-FAILED':
        return respond(400, {'message':'Cannot update unless inspection failed'})

    storing_table.update_item(
        Key={'storing_order_id': sid},
        UpdateExpression="SET discrepancy_detail = :d",
        ExpressionAttributeValues={':d': detail}
    )
    return respond(200, {'message':'Discrepancy updated'})