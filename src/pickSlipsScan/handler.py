import json
import os
import boto3
from decimal import Decimal
import logging
from common.middleware.api_key_middleware import require_api_key
from common.utils import make_response, handle_options

# 로거 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['PICKSLIPS_TABLE'])

def convert_decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(i) for i in obj]
    return obj

@require_api_key('pickslips:scan')
def lambda_handler(event, context):
    logger.info("=== PickSlipsScan 핸들러 시작 ===")
    logger.info(f"이벤트 객체: {json.dumps(event, indent=2)}")
    
    # OPTIONS 요청 처리
    if event.get('httpMethod') == 'OPTIONS':
        logger.info("OPTIONS 요청 감지 - CORS 프리플라이트 처리")
        response = handle_options()
        logger.info(f"OPTIONS 응답: {json.dumps(response, indent=2)}")
        return response
        
    try:
        logger.info("DynamoDB 스캔 시작")
        response = table.scan()
        items = convert_decimal_to_float(response.get('Items', []))
        logger.info(f"스캔 결과 항목 수: {len(items)}")
        logger.debug(f"스캔 결과 데이터: {json.dumps(items, indent=2)}")
        
        final_response = make_response(200, {'data': items})
        logger.info(f"최종 응답: {json.dumps(final_response, indent=2)}")
        return final_response
        
    except Exception as e:
        logger.error(f"오류 발생: {str(e)}", exc_info=True)
        error_response = make_response(500, {'message': 'Internal Server Error'})
        logger.info(f"에러 응답: {json.dumps(error_response, indent=2)}")
        return error_response
    finally:
        logger.info("=== PickSlipsScan 핸들러 종료 ===\n")
