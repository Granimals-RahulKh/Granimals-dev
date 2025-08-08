##---------------------------------------------------------##
##                     register_user.py                    ##
##---------------------------------------------------------##
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
##                     login.py                            ##
##---------------------------------------------------------##
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
##---------------------------------------------------------##
##                     change_password.py                  ##
##---------------------------------------------------------##
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
            f"Please log in and change this password immediately.\n"
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
##---------------------------------------------------------##
##                     insert_diet_plan.py                 ##
##---------------------------------------------------------##
import boto3
import json
import os
import psycopg2
import traceback

# def get_db_credentials(secret_arn):
#     client = boto3.client('secretsmanager')
#     response = client.get_secret_value(SecretId=secret_arn)
#     secret = json.loads(response['SecretString'])
#     return secret

def lambda_handler(event, context):
    try:
        print("Parsing request body...")
        body = json.loads(event.get('body', '{}'))
        print("Parsed body:", body)

        creds = {
            "host": "granimals-dev-cluster-1.cr82g6co4rta.ap-south-1.rds.amazonaws.com",
            "port": 5432,
            "dbname": "granimalsdev",
            "username": "granimals_rds",
            "password": "rdsSecret#1"
        }

        print("Connecting to DB...")
        conn = psycopg2.connect(
            host=creds['host'],
            port=creds['port'],
            dbname=creds['dbname'],
            user=creds['username'],
            password=creds['password']
        )
        cursor = conn.cursor()
        print("Connected to DB")

        if 'diet_plan_id' in body:
            print("Starting insert for diet_plan:", body['diet_plan_id'])
            insert_diet_plan(cursor, body)
        else:
            print("No diet_plan_id found in the body")

        conn.commit()
        print("Transaction committed")

        cursor.close()
        conn.close()
        print("Connection closed")

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Data inserted successfully"})
        }

    except Exception as e:
        print("Exception occurred:", str(e))
        traceback.print_exc()
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }


def insert_diet_plan(cursor, data):
    print("Inserting into diet_plans...")
    cursor.execute("""
        INSERT INTO diet_plans (diet_plan_id, category, support_staff_id)
        VALUES (%s, %s, %s)
    """, (data['diet_plan_id'], data['category'], data['support_staff_id']))

    for week in data.get('weeks', []):
        print("Processing week:", week['diet_week_id'])
        insert_diet_week(cursor, data['diet_plan_id'], week)


def insert_diet_week(cursor, diet_plan_id, week):
    print("Inserting into diet_weeks...")
    cursor.execute("""
        INSERT INTO diet_weeks (diet_week_id, diet_plan_id, week_number)
        VALUES (%s, %s, %s)
    """, (week['diet_week_id'], diet_plan_id, week['week_number']))

    for day in week.get('days', []):
        print("Processing day:", day['diet_day_id'])
        insert_diet_day(cursor, week['diet_week_id'], day)


def insert_diet_day(cursor, diet_week_id, day):
    print("Inserting into diet_days...")
    cursor.execute("""
        INSERT INTO diet_days (diet_day_id, diet_week_id, diet_day_name, date_assigned)
        VALUES (%s, %s, %s, %s)
    """, (day['diet_day_id'], diet_week_id, day['diet_day_name'], day['date_assigned']))

    for meal in day.get('meals', []):
        print("Processing meal:", meal.get('meal_id'))
        insert_diet_meal(cursor, day['diet_day_id'], meal)


def insert_diet_meal(cursor, diet_day_id, meal):
    print("Inserting into diet_meals...")
    cursor.execute("""
        INSERT INTO diet_meals (
            diet_day_id, meal_type, meal_id, meal_name,
            calories, proteins, fibers, fats,
            time_of_meal, status, notes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        diet_day_id,
        meal.get('meal_type'),
        meal.get('meal_id'),
        meal.get('meal_name'),
        meal.get('calories'),
        meal.get('proteins'),
        meal.get('Fibers') or meal.get('fibers'),
        meal.get('fats'),
        meal.get('time_of_meal'),
        meal.get('status'),
        json.dumps(meal.get('notes', []))
    ))
##---------------------------------------------------------##
##                     insert_diet_plan.json               ##
##---------------------------------------------------------##
{
  "body": "{\n  \"diet_plan_id\": \"c73b88a3-5705-4aa3-8b38-76884937b15d\",\n  \"category\": \"custom\",\n  \"support_staff_id\": \"ac9e3811-78d4-4c10-b835-eede5f62cd5b\",\n  \"weeks\": [\n    {\n      \"diet_week_id\": \"9c3f6dd2-06e3-4ac5-bafe-1b781fe6a111\",\n      \"week_number\": 1,\n      \"days\": [\n        {\n          \"diet_day_id\": \"c289d7f3-2d6d-4b3f-889e-f3dcd66c96f2\",\n          \"diet_day_name\": \"monday\",\n          \"date_assigned\": \"2025-05-26\",\n          \"meals\": [\n            {\n              \"meal_type\": \"breakfast\",\n              \"meal_id\": \"dish001\",\n              \"meal_name\": \"Oats\",\n              \"time_of_meal\": \"08:00\",\n              \"status\": \"not complete\",\n              \"notes\": [\"high fiber\"]\n            }\n          ]\n        }\n      ]\n    }\n  ]\n}"
}

##---------------------------------------------------------##
##                     creating tables query               ##
##---------------------------------------------------------##
CREATE TABLE diet_plans (
    diet_plan_id UUID PRIMARY KEY,
    category TEXT,
    support_staff_id UUID
);

CREATE TABLE diet_weeks (
    diet_week_id UUID PRIMARY KEY,
    diet_plan_id UUID REFERENCES diet_plans(diet_plan_id),
    week_number INT
);

CREATE TABLE diet_days (
    diet_day_id UUID PRIMARY KEY,
    diet_week_id UUID REFERENCES diet_weeks(diet_week_id),
    diet_day_name TEXT,
    date_assigned DATE
);

CREATE TABLE diet_meals (
    id SERIAL PRIMARY KEY,
    diet_day_id UUID REFERENCES diet_days(diet_day_id),
    meal_type TEXT,
    meal_id TEXT,
    meal_name TEXT,
    calories TEXT,
    proteins TEXT,
    fibers TEXT,
    fats TEXT,
    time_of_meal TEXT,
    status TEXT,
    notes JSONB
);
##---------------------------------------------------------##
##            Quick Pritunl Install Commands               ##
##---------------------------------------------------------##
sudo apt update && sudo apt install -y curl gnupg
curl -fsSL https://pgp.mongodb.com/server-6.0.asc | \
  sudo gpg -o /usr/share/keyrings/mongodb-server-6.0.gpg --dearmor
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | \
  sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
echo "deb https://repo.pritunl.com/stable/apt jammy main" | \
  sudo tee /etc/apt/sources.list.d/pritunl.list
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv-keys 7568D9BB55FF9E5287D586017AE645C0CF8E292A
sudo apt update
sudo apt install -y mongodb-org pritunl
sudo systemctl enable mongod pritunl
sudo systemctl start mongod pritunl