from typing import List, Optional
from ..models.api_key import APIKey
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime

class APIKeyRepository:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('api_keys')

    def create_api_key(self, api_key: APIKey) -> APIKey:
        item = api_key.dict()
        item['created_at'] = item['created_at'].isoformat()
        if item.get('expires_at'):
            item['expires_at'] = item['expires_at'].isoformat()
        
        self.table.put_item(Item=item)
        return api_key

    def get_api_key_by_key(self, key: str) -> Optional[APIKey]:
        response = self.table.query(
            IndexName='key-index',
            KeyConditionExpression=Key('key').eq(key)
        )
        
        items = response.get('Items', [])
        if not items:
            return None
            
        item = items[0]
        item['created_at'] = datetime.fromisoformat(item['created_at'])
        if item.get('expires_at'):
            item['expires_at'] = datetime.fromisoformat(item['expires_at'])
            
        return APIKey(**item)

    def validate_api_key(self, key: str, required_permission: str) -> bool:
        api_key = self.get_api_key_by_key(key)
        
        if not api_key:
            return False
            
        if not api_key.is_active:
            return False
            
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return False
            
        return required_permission in api_key.permissions 