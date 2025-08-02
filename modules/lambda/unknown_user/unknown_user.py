import os
import json
import boto3

cognito_idp = boto3.client('cognito-idp')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    user_pool_id = os.environ.get('USER_POOL_ID')
    register_function_name = os.environ.get('REGISTER_FUNCTION_NAME')

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
    password = event.get('password', 'TempPass123!')
    group = event.get('group', 'user')

    if not user_pool_id or not username or not group:
        return {
            'statusCode': 400,
            'body': json.dumps({"message": 'Missing "username" or "group" in the request'})
        }

    try:
        # Register the user
        cognito_idp.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username,
            TemporaryPassword=password,
            UserAttributes=[
                {'Name': 'email', 'Value': username},
                {'Name': 'email_verified', 'Value': 'True'}
            ],
            MessageAction='SUPPRESS'  # Do not send welcome email
        )

        # Set a permanent password
        cognito_idp.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=username,
            Password=password,
            Permanent=True
        )

        # Add user to group
        cognito_idp.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username=username,
            GroupName=group
        )

        # Optional: Trigger another Lambda if required (for chaining logic)
        if register_function_name:
            lambda_client.invoke(
                FunctionName=register_function_name,
                InvocationType='Event',
                Payload=json.dumps({
                    "action": "registered",
                    "username": username
                }).encode()
            )

        return {
            'statusCode': 200,
            'body': json.dumps({"message": f"User '{username}' registered successfully"})
        }

    except Exception as e:
        print(f"❌ Registration error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({"message": f"Internal server error: {str(e)}"})
        }