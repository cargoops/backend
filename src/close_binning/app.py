import json
import os
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
packages_table_name = os.environ.get('PACKAGES_TABLE')
packages_table = dynamodb.Table(packages_table_name)

def lambda_handler(event, context):
    print(f"Lambda function started - Event: {json.dumps(event)}")
    try:
        if event.get('httpMethod', 'POST') == 'GET':
            params = event.get('queryStringParameters') or {}
            role = params.get('role')
            employee_id = params.get('employee_id')
            path_params = event.get('pathParameters', {})
        else:
            body = json.loads(event.get('body', '{}'))
            role = body.get('role')
            employee_id = body.get('employee_id')
            path_params = event.get('pathParameters', {})
        if role != 'binner':
            return {
                'statusCode': 403,
                'body': json.dumps({'message': f"Forbidden: Role '{role}' is not authorized."})
            }
        package_id = path_params.get('package_id')
        if not package_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Bad Request: package_id is required.'})
            }

        # Check if the package exists
        print(f"Checking if package {package_id} exists in DynamoDB")
        item_response = packages_table.get_item(Key={'package_id': package_id}, ConsistentRead=True)
        if 'Item' not in item_response:
            print(f"Package {package_id} not found in database")
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'Not Found: Package not found.'})
            }

        print(f"Package {package_id} found, updating status to BINNED")
        # bin_allocation, product_id 읽기
        package_item = item_response['Item']
        bin_allocation_str = package_item.get('bin_allocation')
        product_id = package_item.get('product_id')
        if not bin_allocation_str or not product_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Bad Request: bin_allocation or product_id missing in package.'})
            }
        try:
            bin_allocation = json.loads(bin_allocation_str.replace("'", '"')) if isinstance(bin_allocation_str, str) else bin_allocation_str
        except Exception as e:
            print(f"bin_allocation 파싱 오류: {e}")
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Bad Request: bin_allocation parsing error.'})
            }
        # inventory 테이블 업데이트
        inventory_table_name = os.environ.get('INVENTORY_TABLE')
        inventory_table = dynamodb.Table(inventory_table_name)
        for bin_id, qty in bin_allocation.items():
            if not isinstance(qty, int):
                try:
                    qty = int(qty)
                except:
                    continue
            # 기존 레코드 조회
            inv_resp = inventory_table.get_item(Key={'bin_id': bin_id, 'product_id': product_id}, ConsistentRead=True)
            if 'Item' in inv_resp:
                # 기존 quantity에 더하기
                prev_qty = inv_resp['Item'].get('quantity', 0)
                new_qty = prev_qty + qty
                inventory_table.update_item(
                    Key={'bin_id': bin_id, 'product_id': product_id},
                    UpdateExpression="SET quantity = :q",
                    ExpressionAttributeValues={':q': new_qty}
                )
                print(f"Updated inventory: bin_id={bin_id}, product_id={product_id}, quantity={prev_qty} -> {new_qty}")
            else:
                # 새로 생성
                inventory_table.put_item(Item={
                    'bin_id': bin_id,
                    'product_id': product_id,
                    'quantity': qty
                })
                print(f"Created inventory: bin_id={bin_id}, product_id={product_id}, quantity={qty}")
        # 패키지 상태 업데이트
        timestamp = datetime.now().isoformat()
        packages_table.update_item(
            Key={'package_id': package_id},
            UpdateExpression="SET #status_attr = :status, binned_date = :date",
            ExpressionAttributeNames={'#status_attr': 'status'},
            ExpressionAttributeValues={
                ':status': 'BINNED',
                ':date': timestamp
            }
        )
        print(f"Successfully updated package {package_id} to BINNED status at {timestamp}")

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({'message': f'Package {package_id} has been binned successfully.'})
        }

    except Exception as e:
        print(f"Error occurred: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error'})
        } 