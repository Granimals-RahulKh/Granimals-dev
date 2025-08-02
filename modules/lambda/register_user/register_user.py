import json
import boto3
import os
import secrets
import string

cognito_idp = boto3.client('cognito-idp')
ses_client = boto3.client('ses')
USER_POOL_ID = os.environ['USER_POOL_ID']
FROM_EMAIL = os.environ['FROM_EMAIL']

def generate_secure_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(secrets.choice(chars) for _ in range(length))

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        username = body.get('username')
        group = body.get('group')

        if not username or not group:
            return {"statusCode": 400, "body": json.dumps("Missing 'username' or 'group' in the request")}

        # Generate secure temporary password
        temp_password = generate_secure_password()

        # Create the user with suppressed message
        cognito_idp.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=username,
            TemporaryPassword=temp_password,
            UserAttributes=[
                {"Name": "email", "Value": username},
                {"Name": "email_verified", "Value": "true"}
            ],
            MessageAction='SUPPRESS'
        )

        # Add user to the specified group
        cognito_idp.admin_add_user_to_group(
            UserPoolId=USER_POOL_ID,
            Username=username,
            GroupName=group
        )

        # Send welcome email with credentials
        email_subject = "Welcome to the Platform – Your Account Details"
        email_body = (
            f"Dear User,\n\n"
            f"Your account has been successfully created and added to the group '{group}'.\n\n"
            f"Login Credentials:\n"
            f"Email: {username}\n"
            f"Temporary Password: {temp_password}\n\n"
            f"Please log in and change your password at your earliest convenience.\n"
            f"For security, do not share these credentials with anyone.\n\n"
            f"Regards,\n"
            f"Support Team"
        )

        ses_client.send_email(
            Source=FROM_EMAIL,
            Destination={'ToAddresses': [username]},
            Message={
                'Subject': {'Data': email_subject},
                'Body': {'Text': {'Data': email_body}}
            }
        )

        return {
            "statusCode": 200,
            "body": json.dumps(f"User '{username}' registered and email sent successfully")
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(str(e))
        }
