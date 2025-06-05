import json
import random
import datetime
from common.utils import packages_table, items_table, bins_table, products_table, respond
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
    product_id = package.get('product_id')
    product = products_table.get_item(Key={'product_id': product_id})
    if not product:
        return respond(404, {'message': '해당 product_id의 상품을 찾을 수 없습니다.'})
    product_volume = product.get('volume')
    total_volume = product_volume * quantity

    rfid_ids_str = package.get('rfid_ids', '').strip('[]')
    rfid_ids = [x for x in rfid_ids_str.split(';') if x]
    status = package.get('status')

    # 4. 상태 체크
    if status != 'READY-FOR-BIN-ALLOCATION':
        return respond(400, {'message': f"패키지 상태가 READY-FOR-BIN-ALLOCATION이 아닙니다. (현재 상태: {status})"})

    # 5. 공간 부족 체크
    if quantity is None:
        return respond(400, {'message': '패키지의 quantity 정보가 없습니다.'})

    # 6. BIN 할당
    # 모든 bin 정보 조회
    bins_response = bins_table.scan()
    bins = bins_response.get('Items', [])
    
    # availability_vol 기준으로 정렬
    bins.sort(key=lambda x: x.get('availability_vol', 0), reverse=True)
    
    bin_allocation = {}
    remaining_quantity = int(quantity)
    
    # 단일 bin에 전체 수량이 들어갈 수 있는지 확인
    for bin in bins:
        if bin.get('availability_vol', 0) >= total_volume:
            bin_id = bin['bin_id']
            bin_allocation = {bin_id: remaining_quantity}
            break
    else:
        # 여러 bin에 분배
        for bin in bins:
            if remaining_quantity <= 0:
                break
                
            bin_id = bin['bin_id']
            bin_volume = bin.get('availability_vol', 0)
            max_items = min(remaining_quantity, int(bin_volume / product_volume))
            
            if max_items > 0:
                bin_allocation[bin_id] = max_items
                remaining_quantity -= max_items
    
    if remaining_quantity > 0:
        return respond(400, {'message': 'Not enough space for bin allocation.'})
        
    bin_allocation_str = json.dumps(bin_allocation)
    now = datetime.datetime.utcnow().isoformat()

    # 패키지 테이블 업데이트
    packages_table.update_item(
        Key={'package_id': package_id},
        UpdateExpression="SET bin_allocation=:ba, binner_id=:bid, bin_allocation_date=:dt, #s=:s",
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={
            ':ba': bin_allocation_str,
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

    return respond(200, {'message': 'Bin allocation 완료', 'bin_id': bin_id, 'quantity': int(quantity)})
