import json

def make_response(status_code: int, body: dict):
    return {
        "statusCode": status_code,
        "body": json.dumps(body),
        "headers": {
            "Content-Type": "application/json"
        }
    }
