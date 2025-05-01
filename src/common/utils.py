import json

def make_response(status_code: int, body: dict = None):
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,x-api-key",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        "Access-Control-Max-Age": "600",
        "Access-Control-Allow-Credentials": "true"
    }
    
    response = {
        "statusCode": status_code,
        "headers": headers
    }
    
    if body is not None:
        response["body"] = json.dumps(body)
    
    return response

def handle_options():
    return make_response(200)
