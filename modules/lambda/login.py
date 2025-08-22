import os
import json
import boto3
from botocore.exceptions import ClientError
import hmac
import hashlib
import base64

def get_secret_hash(username, client_id, client_secret):
    message = username + client_id
    dig = hmac.new(
        client_secret.encode('utf-8'),
        msg=message.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()

cognito_idp = boto3.client('cognito-idp', region_name='ap-south-1')

def lambda_handler(event, context):
    user_pool_id = os.environ.get('USER_POOL_ID')
    client_id = os.environ.get('USER_POOL_CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')  # ✅ New addition

    # Parse JSON body if coming from API Gateway
    if isinstance(event, dict) and "body" in event:
        try:
            event = json.loads(event["body"])
        except Exception:
            return {
                'statusCode': 400,
                'body': json.dumps({"message": "Invalid JSON in request body"})
            }

    username = event.get('username')
    password = event.get('password')

    if not user_pool_id or not client_id or not username or not password:
        return {
            'statusCode': 400,
            'body': json.dumps({"message": 'Missing "username" or "password" in the request'})
        }

    # Step 1: Check if user exists
    try:
        cognito_idp.admin_get_user(
            UserPoolId=user_pool_id,
            Username=username
        )
    except cognito_idp.exceptions.UserNotFoundException:
        return {
            'statusCode': 404,
            'body': json.dumps({"message": "failure!"})
        }
    except ClientError as e:
        print(f"❌ Error checking user: {e.response['Error']['Message']}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                "message": f"Internal error checking user existence: {e.response['Error']['Message']}"
            })
        }

    # Step 2: Try authenticating user
    try:
        auth_params = {
            'USERNAME': username,
            'PASSWORD': password
        }

        # ✅ Add SECRET_HASH if client_secret is provided
        if client_secret:
            auth_params['SECRET_HASH'] = get_secret_hash(username, client_id, client_secret)

        auth_response = cognito_idp.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters=auth_params
        )

        # Step 3: Get group
        group_response = cognito_idp.admin_list_groups_for_user(
            UserPoolId=user_pool_id,
            Username=username
        )
        groups = group_response.get("Groups", [])
        group_name = groups[0]["GroupName"] if groups else "user"

        return {
            'statusCode': 200,
            'body': json.dumps({
                "message": "success!",
                "group": group_name
            })
        }

    except cognito_idp.exceptions.NotAuthorizedException:
        return {
            'statusCode': 401,
            'body': json.dumps({"message": "Incorrect username or password. Please try again."})
        }

    except cognito_idp.exceptions.UserNotConfirmedException:
        return {
            'statusCode': 403,
            'body': json.dumps({"message": "User not confirmed. Please verify your email before logging in."})
        }

    except ClientError as e:
        print(f"❌ Login error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({"message": "An unexpected error occurred during login."})
        }
