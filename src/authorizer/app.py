import json
from common.utils import get_api_key_record

def generate_policy(principal, effect, resource, context=None):
    policy = {
        'principalId': principal,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action':   'execute-api:Invoke',
                'Effect':   effect,
                'Resource': resource
            }]
        }
    }
    if context:
        policy['context'] = context
    return policy

def lambda_handler(event, context):
    token = event['headers'].get('x-api-key')
    print(event)
    if not token:
        return generate_policy('anon','Deny', event['methodArn'])

    rec = get_api_key_record(token)
    if not rec:
        return generate_policy('anon','Deny', event['methodArn'])

    # allow—and pass back employee_id & role
    return generate_policy(
      rec['employee_id'],
      'Allow',
      event['methodArn'],
      context={'employee_id': rec['employee_id'], 'role': rec['role']}
    )
