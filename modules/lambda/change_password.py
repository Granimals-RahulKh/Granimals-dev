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
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('username')  # consistent naming

        if not email:
            return {
                "statusCode": 400,
                "body": json.dumps("Missing 'username' (email) in the request")
            }

        # Check if the user exists in Cognito
        try:
            cognito_idp.admin_get_user(
                UserPoolId=USER_POOL_ID,
                Username=email
            )
        except cognito_idp.exceptions.UserNotFoundException:
            return {
                "statusCode": 404,
                "body": json.dumps(f"No user found with username/email: {email}")
            }

        # Generate new secure password
        new_password = generate_secure_password()

        # Set the new password
        cognito_idp.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=email,
            Password=new_password,
            Permanent=True
        )

        # Send email via SES
        email_subject = "Your Password Has Been Reset"
        email_body = (
            f"Dear User,\n\n"
            f"Your password has been successfully reset.\n\n"
            f"Username: {email}\n"
            f"New Password: {new_password}\n\n"
            f"Keep this information secure and do not share it with anyone.\n\n"
            f"Regards,\nSupport Team"
        )

        ses_client.send_email(
            Source=FROM_EMAIL,
            Destination={'ToAddresses': [email]},
            Message={
                'Subject': {'Data': email_subject},
                'Body': {
                    'Text': {'Data': email_body}
                }
            }
        )

        return {
            "statusCode": 200,
            "body": json.dumps(f"New password has been set and emailed to {email}")
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(str(e))
        }
