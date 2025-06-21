import json
from common.utils import api_keys_table, respond

def lambda_handler(event, context):
    # 쿼리스트링 또는 body에서 api_key 추출
    api_key = None
    if event.get('queryStringParameters') and event['queryStringParameters'].get('api_key'):
        api_key = event['queryStringParameters']['api_key']
    elif event.get('body'):
        try:
            body = json.loads(event['body'])
            api_key = body.get('api_key')
        except Exception:
            pass

    if not api_key:
        return respond(400, {'message': 'api_key is required'})

    rec = api_keys_table.get_item(Key={'api_key': api_key}, ConsistentRead=True).get('Item')
    if not rec:
        return respond(404, {'message': 'Not found'})

    return respond(200, rec)