import json

def make_response(status_code: int, body: dict = None):
    headers = {
        "Content-Type": "application/json"
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
