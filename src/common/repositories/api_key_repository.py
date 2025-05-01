from typing import List, Optional
from common.models.api_key import APIKey
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
import logging

# 로거 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class APIKeyRepository:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('api_keys')

    def create_api_key(self, api_key: APIKey) -> APIKey:
        logger.info(f"API 키 생성 시작: {api_key.id}")
        item = api_key.dict()
        item['created_at'] = item['created_at'].isoformat()
        if item.get('expires_at'):
            item['expires_at'] = item['expires_at'].isoformat()
        
        self.table.put_item(Item=item)
        logger.info(f"API 키 생성 완료: {api_key.id}")
        return api_key

    def get_api_key_by_key(self, key: str) -> Optional[APIKey]:
        logger.info(f"API 키 조회 시작: {key}")
        response = self.table.query(
            IndexName='key-index',
            KeyConditionExpression=Key('key').eq(key)
        )
        
        items = response.get('Items', [])
        if not items:
            logger.warning(f"API 키를 찾을 수 없음: {key}")
            return None
            
        item = items[0]
        logger.info(f"API 키 조회 결과: {item}")
        
        item['created_at'] = datetime.fromisoformat(item['created_at'])
        if item.get('expires_at'):
            item['expires_at'] = datetime.fromisoformat(item['expires_at'])
            
        return APIKey(**item)

    def validate_api_key(self, key: str, required_permission: str) -> bool:
        logger.info(f"API 키 검증 시작 - 키: {key}, 필요 권한: {required_permission}")
        
        api_key = self.get_api_key_by_key(key)
        
        if not api_key:
            logger.warning("API 키가 존재하지 않음")
            return False
            
        if not api_key.is_active:
            logger.warning("API 키가 비활성화 상태")
            return False
            
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            logger.warning("API 키가 만료됨")
            return False
            
        has_permission = required_permission in api_key.permissions
        logger.info(f"권한 검증 결과: {'성공' if has_permission else '실패'}")
        return has_permission 