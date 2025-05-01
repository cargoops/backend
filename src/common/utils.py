import json
import logging

# 로거 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def make_response(status_code: int, body: dict = None):
    logger.info("=== make_response 호출 ===")
    logger.info(f"Status Code: {status_code}")
    logger.info(f"Body: {json.dumps(body, indent=2) if body else 'None'}")
    
    headers = {
        "Content-Type": "application/json"
    }
    
    logger.info("=== 헤더 ===")
    logger.info(json.dumps(headers, indent=2))
    
    response = {
        "statusCode": status_code,
        "headers": headers
    }
    
    if body is not None:
        response["body"] = json.dumps(body)
    
    logger.info("=== 최종 응답 ===")
    logger.info(json.dumps(response, indent=2))
    return response

def handle_options():
    logger.info("=== OPTIONS 요청 처리 ===")
    response = make_response(200)
    logger.info("=== OPTIONS 응답 완료 ===")
    return response
