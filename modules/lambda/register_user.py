import json
import boto3
import os
import secrets
import string
import uuid  # for unique IDs

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
        name = body.get('name')
        group = body.get('group')

        if not username or not group or not name:
            return {
                "statusCode": 400,
                "body": json.dumps("Missing 'username', 'name', or 'group' in the request")
            }

        # Generate secure permanent password
        permanent_password = generate_secure_password()

        # Decide whether to create client_id or support_staff_id
        if group.lower() == "client":
            unique_id = str(uuid.uuid4())
            user_attribute_name = "custom:client_id"
        else:
            unique_id = str(uuid.uuid4())
            user_attribute_name = "custom:support_staff_id"

        # Step 1: Create the user (with a temp password first)
        cognito_idp.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=username,
            TemporaryPassword=permanent_password,  # will be overwritten
            UserAttributes=[
                {"Name": "email", "Value": username},
                {"Name": "email_verified", "Value": "true"},
                {"Name": "name", "Value": name},
                {"Name": user_attribute_name, "Value": unique_id}
            ],
            MessageAction='SUPPRESS'
        )

        # Step 2: Immediately set the password as permanent
        cognito_idp.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=username,
            Password=permanent_password,
            Permanent=True
        )

        # Step 3: Add user to the specified group
        cognito_idp.admin_add_user_to_group(
            UserPoolId=USER_POOL_ID,
            Username=username,
            GroupName=group
        )

        # Step 4: Send welcome email with credentials
        email_subject = "Welcome to the Platform – Your Account Details"
        email_body = (
            f"Dear {name},\n\n"
            f"Your account has been successfully created.\n\n"
            f"Login Credentials:\n"
            f"Email: {username}\n"
            f"Password: {permanent_password}\n"
            f"You can log in directly with these credentials.\n"
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
            "body": json.dumps(
                f"User '{username}' registered with "
                f"{'client_id' if group.lower() == 'client' else 'support_staff_id'} "
                f"'{unique_id}' and permanent password set successfully"
            )
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(str(e))
        }
