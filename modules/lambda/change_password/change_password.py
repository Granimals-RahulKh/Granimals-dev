import json
import boto3
import os

cognito_idp = boto3.client('cognito-idp')
ses_client = boto3.client('ses')
USER_POOL_ID = os.environ['USER_POOL_ID']
FROM_EMAIL = os.environ['FROM_EMAIL']

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        username = body.get('username')
        new_password = body.get('new_password')

        if not username or not new_password:
            return {
                "statusCode": 400,
                "body": json.dumps("Missing 'username' or 'new_password' in the request")
            }

        # Set the new password
        cognito_idp.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=username,
            Password=new_password,
            Permanent=True
        )

        # Send SES email with password
        email_subject = "Your Password Has Been Updated"
        email_body = (
            f"Dear User,\n\n"
            f"Your password has been successfully updated.\n\n"
            f"Username: {username}\n"
            f"New Password: {new_password}\n\n"
            f"Please keep this information secure and do not share it with anyone.\n\n"
            f"Regards,\n"
            f"Support Team"
        )

        ses_client.send_email(
            Source=FROM_EMAIL,
            Destination={'ToAddresses': [username]},
            Message={
                'Subject': {'Data': email_subject},
                'Body': {
                    'Text': {'Data': email_body}
                }
            }
        )

        return {
            "statusCode": 200,
            "body": json.dumps(f"Password changed and email sent to '{username}'")
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(str(e))
        }
