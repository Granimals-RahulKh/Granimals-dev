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
