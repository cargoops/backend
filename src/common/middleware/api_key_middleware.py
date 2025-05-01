from functools import wraps
from typing import Callable
import json
import logging
from common.repositories.api_key_repository import APIKeyRepository
from common.utils import make_response

# 로거 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def require_api_key(required_permission: str):
    def decorator(handler: Callable):
        @wraps(handler)
        def wrapper(event, context):
            logger.info("=== API 키 검증 시작 ===")
            logger.info(f"필요한 권한: {required_permission}")
            logger.info(f"이벤트 헤더: {json.dumps(event.get('headers', {}), indent=2)}")
            
            # OPTIONS 요청은 항상 허용
            if event.get('httpMethod') == 'OPTIONS':
                logger.info("OPTIONS 요청 감지 - 인증 건너뛰기")
                return handler(event, context)

            # API 키 추출
            api_key = event.get('headers', {}).get('x-api-key')
            if not api_key:
                logger.warning("API 키 없음")
                return make_response(401, {'error': 'API key is required'})

            # API 키 검증
            repository = APIKeyRepository()
            if not repository.validate_api_key(api_key, required_permission):
                logger.warning(f"API 키 검증 실패: {api_key}")
                return make_response(403, {'error': 'Invalid API key or insufficient permissions'})

            logger.info("API 키 검증 성공")
            # 핸들러 실행
            return handler(event, context)
        return wrapper
    return decorator 