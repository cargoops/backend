import json
from common.utils import storing_table, respond

def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    role = body.get('role')
    employee_id = body.get('employee_id')
    if role != 'receiver':
        return respond(403, {'message':'Forbidden'})
    try:
        sid = body['storing_order_id']
        detail = body['discrepancy_detail']
    except Exception:
        return respond(400, {'message':'Invalid input'})

    r = storing_table.get_item(Key={'storing_order_id': sid}, ConsistentRead=True)
    order = r.get('Item')
    if not order:
        return respond(404, {'message':'Order not found'})
    if order.get('status') != 'INSPECTION-FAILED':
        return respond(400, {'message':'Cannot update unless inspection failed'})

    storing_table.update_item(
        Key={'storing_order_id': sid},
        UpdateExpression="SET discrepancy_detail = :d, doc_inspection_result = :f",
        ExpressionAttributeValues={':d': detail, ':f': 'Failure'}
    )
    return respond(200, {'message':'Discrepancy updated'})