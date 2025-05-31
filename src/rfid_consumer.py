import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['ITEMS_TABLE'])  # 환경변수로 테이블명 전달 추천

def lambda_handler(event, context):
    for record in event['Records']:
        body = json.loads(record['body'])
        rfid_id = body['rfid_id']
        timestamp = body.get('timestamp')
        # 필요한 추가 필드가 있다면 여기에 추가
        table.put_item(Item={
            'rfid_id': rfid_id,
            'timestamp': timestamp
        })
    return {"statusCode": 200}
