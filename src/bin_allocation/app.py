import json
import random
import datetime
from common.utils import packages_table, items_table, bins_table, products_table, respond
import os
import boto3

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    print("=== Bin Allocation Lambda 시작 ===")
    
    # 1. 인증 및 권한 체크
    auth = event['requestContext'].get('authorizer', {})
    print(f"인증 정보: {auth}")
    if auth.get('role') != 'binner':
        print(f"권한 오류: role={auth.get('role')}")
        return respond(403, {'message': '권한이 없습니다. (role != binner)'})

    # 2. 입력값 파싱
    try:
        body = json.loads(event['body'])
        package_id = body['package_id']
        employee_id = body['employee_id']
        print(f"입력값: package_id={package_id}, employee_id={employee_id}")
    except Exception as e:
        print(f"입력값 파싱 오류: {str(e)}")
        return respond(400, {'message': '입력값이 올바르지 않습니다.'})

    # 3. 패키지 레코드 조회
    print(f"패키지 조회: package_id={package_id}")
    r = packages_table.get_item(Key={'package_id': package_id})
    package = r.get('Item')
    if not package:
        print("패키지를 찾을 수 없음")
        return respond(404, {'message': '해당 package_id의 패키지를 찾을 수 없습니다.'})

    quantity = package.get('quantity')
    product_id = package.get('product_id')
    print(f"패키지 정보: quantity={quantity}, product_id={product_id}")
    
    product = products_table.get_item(Key={'product_id': product_id})
    if not product:
        print(f"상품을 찾을 수 없음: product_id={product_id}")
        return respond(404, {'message': '해당 product_id의 상품을 찾을 수 없습니다.'})
    
    product_volume = product.get('Item', {}).get('volume')
    if product_volume is None:
        print("상품 부피 정보 없음")
        return respond(400, {'message': '상품의 volume 정보가 없습니다.'})
    total_volume = product_volume * quantity
    print(f"부피 정보: product_volume={product_volume}, total_volume={total_volume}")

    rfid_ids_str = package.get('rfid_ids', '').strip('[]')
    rfid_ids = [x for x in rfid_ids_str.split(';') if x]
    status = package.get('status')
    print(f"RFID 및 상태: rfid_ids={rfid_ids}, status={status}")

    # 4. 상태 체크
    if status != 'READY-FOR-BIN-ALLOCATION':
        print(f"상태 오류: 현재 상태={status}")
        return respond(400, {'message': f"패키지 상태가 READY-FOR-BIN-ALLOCATION이 아닙니다. (현재 상태: {status})"})

    # 5. 공간 부족 체크
    if quantity is None:
        print("수량 정보 없음")
        return respond(400, {'message': '패키지의 quantity 정보가 없습니다.'})

    # 6. BIN 할당
    print("BIN 정보 조회 중...")
    bins_response = bins_table.scan()
    bins = bins_response.get('Items', [])
    print(f"조회된 BIN 수: {len(bins)}")
    
    bins.sort(key=lambda x: x.get('availability_vol', 0), reverse=True)
    
    bin_allocation = {}
    remaining_quantity = int(quantity)
    print(f"할당 시작: remaining_quantity={remaining_quantity}")
    
    # 단일 bin에 전체 수량이 들어갈 수 있는지 확인
    for bin in bins:
        if bin.get('availability_vol', 0) >= total_volume:
            bin_id = bin['bin_id']
            bin_allocation = {bin_id: remaining_quantity}
            print(f"단일 BIN 할당: bin_id={bin_id}, quantity={remaining_quantity}")
            remaining_quantity = 0
            break
    else:
        print("여러 BIN에 분배 시작")
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
                print(f"BIN 할당: bin_id={bin_id}, quantity={max_items}, remaining={remaining_quantity}")
    
    if remaining_quantity > 0:
        print(f"공간 부족: remaining_quantity={remaining_quantity}")
        return respond(400, {'message': 'Not enough space for bin allocation.'})
        
    bin_allocation_str = json.dumps(bin_allocation)
    now = datetime.datetime.utcnow().isoformat()
    print(f"최종 BIN 할당: {bin_allocation_str}")

    # BIN별로 availability_vol 업데이트
    for bin_id, allocated_qty in bin_allocation.items():
        used_volume = allocated_qty * product_volume
        bins_table.update_item(
            Key={'bin_id': bin_id},
            UpdateExpression="SET availability_vol = availability_vol - :used",
            ExpressionAttributeValues={':used': used_volume}
        )

    # 패키지 테이블 업데이트
    print("패키지 테이블 업데이트 중...")
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
    print(f"RFID 상태 업데이트 중... (총 {len(rfid_ids)}개)")
    for rfid_id in rfid_ids:
        items_table.update_item(
            Key={'rfid_id': rfid_id},
            UpdateExpression="SET #s=:s",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': 'READY-FOR-BINNING'}
        )

    print("=== Bin Allocation Lambda 완료 ===")
    return respond(200, {'message': 'Bin allocation 완료', 'bin_id': bin_id, 'quantity': int(quantity)})
