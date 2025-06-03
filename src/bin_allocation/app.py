import json
import random
import datetime
from common.utils import packages_table, items_table, respond
import os
import boto3

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    # 1. 인증 및 권한 체크
    auth = event['requestContext'].get('authorizer', {})
    if auth.get('role') != 'binner':
        return respond(403, {'message': '권한이 없습니다. (role != binner)'})

    # 2. 입력값 파싱
    try:
        body = json.loads(event['body'])
        package_id = body['package_id']
        employee_id = body['employee_id']
    except Exception:
        return respond(400, {'message': '입력값이 올바르지 않습니다.'})

    # 3. 패키지 레코드 조회
    r = packages_table.get_item(Key={'package_id': package_id})
    package = r.get('Item')
    if not package:
        return respond(404, {'message': '해당 package_id의 패키지를 찾을 수 없습니다.'})

    quantity = package.get('quantity')
    rfid_ids_str = package.get('rfid_ids', '')
    rfid_ids = [x for x in rfid_ids_str.split(';') if x]
    status = package.get('status')

    # 4. 상태 체크
    if status != 'READY-FOR-BIN-ALLOCATION':
        return respond(400, {'message': f"패키지 상태가 READY-FOR-BIN-ALLOCATION이 아닙니다. (현재 상태: {status})"})

    # 5. 공간 부족 체크
    if quantity is None:
        return respond(400, {'message': '패키지의 quantity 정보가 없습니다.'})
    if int(quantity) >= 50:
        return respond(400, {'message': 'Not enough space for bin allocation.'})

    # 6. BIN 할당
    bin_num = random.randint(1, 5)
    bin_id = f"BIN{bin_num}"
    bin_allocation = json.dumps({bin_id: quantity})
    now = datetime.datetime.utcnow().isoformat()

    # 패키지 테이블 업데이트
    packages_table.update_item(
        Key={'package_id': package_id},
        UpdateExpression="SET bin_allocation=:ba, binner_id=:bid, bin_allocation_date=:dt, #s=:s",
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={
            ':ba': bin_allocation,
            ':bid': employee_id,
            ':dt': now,
            ':s': 'READY-FOR-BINNING'
        }
    )

    # 7. RFID별로 Items 테이블 상태 업데이트
    for rfid_id in rfid_ids:
        items_table.update_item(
            Key={'rfid_id': rfid_id},
            UpdateExpression="SET #s=:s",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': 'READY-FOR-BINNING'}
        )

    return respond(200, {'message': 'Bin allocation 완료', 'bin_id': bin_id, 'quantity': quantity})
