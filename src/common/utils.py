import json

def make_response(status_code: int, body: dict = None):
    print("=== make_response 호출 ===")
    print(f"Status Code: {status_code}")
    print(f"Body: {json.dumps(body, indent=2) if body else 'None'}")
    
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,x-api-key",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        "Access-Control-Max-Age": "600",
        "Access-Control-Allow-Credentials": "true"
    }
    
    print("=== CORS 헤더 ===")
    print(json.dumps(headers, indent=2))
    
    response = {
        "statusCode": status_code,
        "headers": headers
    }
    
    if body is not None:
        response["body"] = json.dumps(body)
    
    print("=== 최종 응답 ===")
    print(json.dumps(response, indent=2))
    return response

def handle_options():
    print("=== OPTIONS 요청 처리 ===")
    response = make_response(200)
    print("=== OPTIONS 응답 완료 ===")
    return response
