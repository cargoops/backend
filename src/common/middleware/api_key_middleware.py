from functools import wraps
from typing import Callable
import json
from common.repositories.api_key_repository import APIKeyRepository

def require_api_key(required_permission: str):
    def decorator(handler: Callable):
        @wraps(handler)
        def wrapper(event, context):
            # API 키 추출
            api_key = event.get('headers', {}).get('x-api-key')
            if not api_key:
                return {
                    'statusCode': 401,
                    'body': json.dumps({
                        'error': 'API key is required'
                    })
                }

            # API 키 검증
            repository = APIKeyRepository()
            if not repository.validate_api_key(api_key, required_permission):
                return {
                    'statusCode': 403,
                    'body': json.dumps({
                        'error': 'Invalid API key or insufficient permissions'
                    })
                }

            # 핸들러 실행
            return handler(event, context)
        return wrapper
    return decorator 