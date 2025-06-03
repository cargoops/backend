import os
import sys
from common.utils import packages_table, respond

def lambda_handler(event, context):
    # event에서 package_id 추출
    package_id = event.get('package_id')
    if not package_id:
        return respond(400, {'error': 'package_id가 필요합니다.'})

    try:
        resp = packages_table.get_item(Key={'package_id': package_id})
        record = resp.get('Item')
        if not record:
            return respond(404, {'error': '해당 package_id의 레코드를 찾을 수 없습니다.'})
        return respond(200, record)
    except Exception as e:
        return respond(500, {'error': str(e)})
