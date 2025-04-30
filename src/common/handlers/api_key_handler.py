import json
from datetime import datetime
from common.models.api_key import APIKey
from common.repositories.api_key_repository import APIKeyRepository
from common.middleware.api_key_middleware import require_api_key

@require_api_key('admin:api_keys')
def create_api_key(event, context):
    try:
        body = json.loads(event['body'])
        
        # API 키 생성
        api_key = APIKey(
            name=body['name'],
            permissions=body['permissions'],
            expires_at=datetime.fromisoformat(body['expires_at']) if body.get('expires_at') else None
        )
        
        # 저장소에 저장
        repository = APIKeyRepository()
        created_key = repository.create_api_key(api_key)
        
        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'API 키가 생성되었습니다.',
                'api_key': {
                    'id': created_key.id,
                    'key': created_key.key,
                    'name': created_key.name,
                    'permissions': created_key.permissions,
                    'expires_at': created_key.expires_at.isoformat() if created_key.expires_at else None
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