##---------------------------------------------------------##
##                     register_user.py                    ##
##---------------------------------------------------------##
import os
import boto3
import json

cognito_idp = boto3.client('cognito-idp')

def lambda_handler(event, context):
    user_pool_id = os.environ.get('USER_POOL_ID')
    username = event.get('username')        # Example: "rahul.k@iamops.io"
    temporary_password = event.get('password', 'TempPass123!')
    group_name = event.get('group')         # e.g., "admin", "support", "customer"

    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': 'Invalid JSON format'
        }

    username = body.get('username')
    temporary_password = body.get('password', 'TempPass123!')
    group_name = body.get('group')
    
    
    # Validate input
    if not user_pool_id:
        return {
            'statusCode': 500,
            'body': 'Missing USER_POOL_ID environment variable'
        }
    
    if not username or not group_name:
        return {
            'statusCode': 400,
            'body': 'Missing "username" or "group" in the request'
        }

    try:
        # Step 1: Create the user
        cognito_idp.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username,
            TemporaryPassword=temporary_password,
            UserAttributes=[
                {'Name': 'email', 'Value': username},
                {'Name': 'email_verified', 'Value': 'true'}
            ],
            MessageAction='SUPPRESS'  # Suppress default email notification
        )
        print(f"✅ User {username} created successfully")

        # Step 2: Add the user to the dynamic group
        cognito_idp.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username=username,
            GroupName=group_name
        )
        print(f"✅ User {username} added to group {group_name}")

        return {
            'statusCode': 200,
            'body': f"User '{username}' created and added to group '{group_name}'"
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            'statusCode': 500,
            'body': f"Error: {str(e)}"
        }


##---------------------------------------------------------##
##                     delete_user.py                      ##
##---------------------------------------------------------##
import os
import boto3
import json

cognito_idp = boto3.client('cognito-idp')

def lambda_handler(event, context):
    user_pool_id = os.environ.get('USER_POOL_ID')
    
    try:
        # Parse body if it's from API Gateway
        if 'body' in event:
            body = json.loads(event['body'])  # Parse string body to dict
        else:
            body = event

        username = body.get('username')

        if not user_pool_id or not username:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing USER_POOL_ID or username'})
            }

        cognito_idp.admin_delete_user(
            UserPoolId=user_pool_id,
            Username=username
        )
        print(f"✅ User {username} deleted from pool {user_pool_id}")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': f"User '{username}' deleted successfully"})
        }

    except Exception as e:
        print(f"❌ Error deleting user: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
##---------------------------------------------------------##
##                     unknown_user.py                     ##
##---------------------------------------------------------##
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
##---------------------------------------------------------##
##                     change_password.py                  ##
##---------------------------------------------------------##
import os
import boto3
import json

cognito_idp = boto3.client('cognito-idp')

def lambda_handler(event, context):
    user_pool_id = os.environ.get('USER_POOL_ID')

    # Ensure body is parsed from API Gateway JSON payload
    try:
        body = json.loads(event.get('body', '{}'))
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON in request body'})
        }

    username = body.get('username')
    new_password = body.get('new_password')

    if not user_pool_id or not username or not new_password:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing USER_POOL_ID, username, or new_password'})
        }

    try:
        cognito_idp.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=username,
            Password=new_password,
            Permanent=True
        )
        print(f"✅ Password updated for user {username}")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': f"Password for user '{username}' changed successfully"})
        }

    except Exception as e:
        print(f"❌ Error changing password: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }