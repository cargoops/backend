import json
import os
from datetime import datetime
import uuid
import boto3
from common.models.api_key import APIKey

def lambda_handler(event, context):
    try:
        # 초기 관리자 API 키 생성
        admin_key = APIKey(
            id=str(uuid.uuid4()),
            key="admin-key-" + str(uuid.uuid4()),
            name="Initial Admin API Key",
            permissions=["admin:api_keys", "storing:check", "packages:read", "pickslips:read", "storing:read"],
            created_at=datetime.utcnow(),
            expires_at=datetime(2025, 12, 31, 23, 59, 59),
            is_active=True
        )
        
        # DynamoDB에 저장
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ['API_KEYS_TABLE'])
        
        item = admin_key.dict()
        item['created_at'] = item['created_at'].isoformat()
        item['expires_at'] = item['expires_at'].isoformat()
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': '초기 관리자 API 키가 생성되었습니다.',
                'api_key': {
                    'id': admin_key.id,
                    'key': admin_key.key,
                    'name': admin_key.name,
                    'permissions': admin_key.permissions,
                    'expires_at': admin_key.expires_at.isoformat()
                }
            })
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        } 