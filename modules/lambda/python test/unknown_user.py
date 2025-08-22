##---------------------------------------------------------##
##                     register_user.py                    ##
##---------------------------------------------------------##
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
sudo pritunl setup-key
sudo pritunl default-password

##---------------------------------------------------------##
##                     Push_data_to_rds                    ##
##---------------------------------------------------------##
import json
import psycopg2
import uuid
import traceback

def lambda_handler(event, context):
    try:
        print("📥 Incoming event:", event)

        # Parse request body
        body = json.loads(event.get("body", "[]"))
        print("📦 Parsed body:", body)

        if isinstance(body, dict):
            inserts = [body]
        elif isinstance(body, list):
            inserts = body
        else:
            error_msg = "Invalid payload format. Must be object or array."
            print("❌ Error:", error_msg)
            return {
                "statusCode": 400,
                "body": json.dumps({"error": error_msg})
            }

        # Database connection details
        creds = {
            "host": "granimals-dev-cluster-1.cr82g6co4rta.ap-south-1.rds.amazonaws.com",
            "port": 5432,
            "dbname": "granimalsdev",
            "username": "granimals_rds",
            "password": "rdsSecret#1"
        }

        print("🔗 Connecting to PostgreSQL...")
        conn = psycopg2.connect(
            host=creds['host'],
            port=creds['port'],
            dbname=creds['dbname'],
            user=creds['username'],
            password=creds['password']
        )
        conn.autocommit = True  # ✅ Run each statement in its own transaction
        cur = conn.cursor()
        print("✅ Database connection established")

        results = []

        for item in inserts:
            table_name = item.get("table_name")
            data = item.get("data", {})

            print(f"\n➡️ Processing insert for table: {table_name}")

            if not table_name or not data:
                error_msg = "Missing table_name or data"
                print(f"❌ Error for {table_name}: {error_msg}")
                results.append({
                    "table": table_name or "unknown",
                    "status": "failed",
                    "error": error_msg
                })
                continue

            # Normalize → always a list of rows
            rows = data if isinstance(data, list) else [data]

            for row in rows:
                try:
                    # ✅ UUID validation
                    for key, value in row.items():
                        if (
                            "id" in key.lower()
                            and isinstance(value, str)
                            and len(value) == 36
                            and value.count("-") == 4
                        ):
                            try:
                                row[key] = str(uuid.UUID(value))
                            except ValueError:
                                error_msg = f"Invalid UUID format for '{key}'"
                                print(f"❌ {error_msg}")
                                results.append({
                                    "table": table_name,
                                    "status": "failed",
                                    "error": error_msg
                                })
                                raise  # Skip insert for this row

                    # Build insert query
                    fields = ", ".join(row.keys())
                    placeholders = ", ".join(["%s"] * len(row))
                    values = list(row.values())
                    query = f"INSERT INTO {table_name} ({fields}) VALUES ({placeholders})"

                    print(f"📝 Executing query: {query} with values {values}")
                    cur.execute(query, values)

                    print(f"✅ Insert successful for table {table_name}")
                    results.append({"table": table_name, "status": "success"})

                except Exception as e:
                    error_msg = str(e)
                    print(f"❌ Insert failed for {table_name}: {error_msg}")
                    print("🔍 Traceback:", traceback.format_exc())
                    results.append({
                        "table": table_name,
                        "status": "failed",
                        "error": error_msg
                    })

        cur.close()
        conn.close()
        print("🔒 Connection closed")

        return {
            "statusCode": 200,
            "body": json.dumps({"results": results})
        }

    except Exception as e:
        error_msg = str(e)
        print("🔥 Fatal error in lambda_handler:", error_msg)
        print("🔍 Traceback:", traceback.format_exc())
        return {
            "statusCode": 500,
            "body": json.dumps({"error": error_msg})
        }
##---------------------------------------------------------##
##              PAYLOAD for Push_data_to_rds               ##
##---------------------------------------------------------##
[
  {
    "table_name": "support_staff",
    "data": {
      "staff_id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "John Doe",
      "role": "Technical Support",
      "email": "john.doe@example.com",
      "phone": "+91-9876543210"
    }
  },
  {
    "table_name": "programs",
    "data": {
      "program_id": "123e4567-e89b-12d3-a456-426614174010",
      "program_name": "Weight Loss Program",
      "description": "A 12-week guided weight loss program."
    }
  },
  {
    "table_name": "phases",
    "data": {
      "phase_id": "123e4567-e89b-12d3-a456-426614174020",
      "phase_name": "Phase 1 - Kickstart",
      "program_id": "123e4567-e89b-12d3-a456-426614174010"
    }
  },
  {
    "table_name": "weeks",
    "data": {
      "week_id": "123e4567-e89b-12d3-a456-426614174030",
      "phase_id": "123e4567-e89b-12d3-a456-426614174020",
      "week_number": 1
    }
  },
  {
    "table_name": "days",
    "data": {
      "day_id": "123e4567-e89b-12d3-a456-426614174040",
      "week_id": "123e4567-e89b-12d3-a456-426614174030",
      "day_number": 1
    }
  },
  {
    "table_name": "exercises",
    "data": {
      "exercise_id": "123e4567-e89b-12d3-a456-426614174050",
      "exercise_name": "Push Ups",
      "description": "Standard push ups for chest and triceps.",
      "sets": 3,
      "reps": 15
    }
  },
  {
    "table_name": "diet_plans",
    "data": {
      "diet_plan_id": "123e4567-e89b-12d3-a456-426614174060",
      "diet_plan_name": "Basic Diet Plan",
      "program_id": "123e4567-e89b-12d3-a456-426614174010"
    }
  },
  {
    "table_name": "meals",
    "data": {
      "meal_id": "123e4567-e89b-12d3-a456-426614174070",
      "meal_name": "Breakfast",
      "calories": 350
    }
  },
  {
    "table_name": "client",
    "data": {
      "client_id": "123e4567-e89b-12d3-a456-426614174080",
      "name": "Alice Smith",
      "diet_plan_id": "123e4567-e89b-12d3-a456-426614174060"
    }
  },
  {
    "table_name": "exercise_feedback",
    "data": {
      "feedback_id": "123e4567-e89b-12d3-a456-426614174090",
      "exercise_id": "123e4567-e89b-12d3-a456-426614174050",
      "client_id": "123e4567-e89b-12d3-a456-426614174080",
      "feedback": "Felt great after doing push ups."
    }
  }
]
##---------------------------------------------------------##
##                     Pull_data_to_rds                    ##
##---------------------------------------------------------##
    import json
import psycopg2
import os
import re
from decimal import Decimal
from datetime import datetime, date

# ==========================================================
# Custom JSON encoder (handles Decimal + datetime types)
# ==========================================================
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


# ==========================================================
# Regex pattern for identifier validation
# ==========================================================
identifier_pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def validate_identifier(identifier, name_type="identifier"):
    if not identifier_pattern.match(identifier):
        raise ValueError(f"Invalid {name_type}: {identifier}")
    return identifier


# ==========================================================
# Main Lambda Handler
# ==========================================================
def lambda_handler(event, context):
    print("📥 Incoming event:", json.dumps(event))  # full payload log

    try:
        body = json.loads(event.get("body", "{}"))
        print("📦 Parsed body:", body)

        query = None
        params = []

        # --------------------------------------------------
        # Case 1: Single-table fallback
        # --------------------------------------------------
        if "table_name" in body:
            print("🔎 Single-table query mode")

            table_name = validate_identifier(body.get("table_name"))
            lookup_field = body.get("lookup_field")
            lookup_value = body.get("lookup_value")

            if lookup_field:
                validate_identifier(lookup_field, "column")
                query = f"SELECT * FROM {table_name} WHERE {lookup_field} = %s"
                params = (lookup_value,)
            else:
                query = f"SELECT * FROM {table_name}"
                params = ()

        # --------------------------------------------------
        # Case 2: Multi-table join mode
        # --------------------------------------------------
        elif "tables" in body and isinstance(body["tables"], list):
            print("🔗 Multi-table query mode")

            tables = body["tables"]
            joins = body.get("join", {})

            select_parts = []
            table_alias_map = {}
            where_clauses = []

            # Assign aliases and build column selections
            for idx, tbl in enumerate(tables):
                table_name = validate_identifier(tbl["name"], "table")
                alias = f"t{idx+1}"
                table_alias_map[table_name] = alias

                cols = tbl.get("columns", ["*"])
                if cols == ["*"]:
                    select_parts.append(f"{alias}.*")
                else:
                    for col in cols:
                        validate_identifier(col, "column")
                        select_parts.append(f"{alias}.{col}")

                # Add filters if any
                filters = tbl.get("filters", {})
                for col, val in filters.items():
                    validate_identifier(col, "column")
                    where_clauses.append(f"{alias}.{col} = %s")
                    params.append(val)

            # Build FROM + JOIN clauses
            from_clause = ""
            join_clauses = []

            if joins and "on" in joins and joins["on"]:
                print("🧩 Explicit join provided:", joins)

                join_type = joins.get("type", "INNER").upper()
                if join_type not in ("INNER", "LEFT", "RIGHT", "FULL", "CROSS"):
                    raise ValueError(f"Invalid join type: {join_type}")

                # First table is FROM
                first_table = validate_identifier(tables[0]["name"], "table")
                from_clause = f"{first_table} {table_alias_map[first_table]}"

                for join in joins["on"]:
                    lt = validate_identifier(join["left_table"], "table")
                    lc = validate_identifier(join["left_column"], "column")
                    rt = validate_identifier(join["right_table"], "table")
                    rc = validate_identifier(join["right_column"], "column")

                    left_alias = table_alias_map.get(lt)
                    right_alias = table_alias_map.get(rt)
                    if not left_alias or not right_alias:
                        raise ValueError(f"Join table not in 'tables' list: {lt}, {rt}")

                    if join_type == "CROSS":
                        join_clause = f"CROSS JOIN {rt} {right_alias}"
                    else:
                        join_clause = (
                            f"{join_type} JOIN {rt} {right_alias} "
                            f"ON {left_alias}.{lc} = {right_alias}.{rc}"
                        )
                    join_clauses.append(join_clause)
            else:
                print("⚡ No join provided → using CROSS JOIN")
                from_parts = []
                for idx, tbl in enumerate(tables):
                    table_name = validate_identifier(tbl["name"], "table")
                    alias = f"t{idx+1}"
                    from_parts.append(f"{table_name} {alias}")
                from_clause = ", ".join(from_parts)

            # Final query
            query = f"SELECT {', '.join(select_parts)} FROM {from_clause} {' '.join(join_clauses)}"
            if where_clauses:
                query += f" WHERE {' AND '.join(where_clauses)}"

        else:
            print("❌ Invalid request format:", body)
            return {"statusCode": 400, "body": json.dumps({"error": "Invalid request format"})}

        print("📝 Final SQL Query:", query)
        print("🔑 Query Params:", params)

        # --------------------------------------------------
        # Database connection
        # --------------------------------------------------
        creds = {
            "host": "granimals-dev-cluster-1.cr82g6co4rta.ap-south-1.rds.amazonaws.com",
            "port": 5432,
            "dbname": "granimalsdev",
            "username": "granimals_rds",
            "password": "rdsSecret#1"
        }

        print("🌐 Connecting to DB:", creds["host"], creds["dbname"])
        conn = psycopg2.connect(
            host=creds["host"],
            port=creds["port"],
            dbname=creds["dbname"],
            user=creds["username"],
            password=creds["password"]
        )
        cur = conn.cursor()

        print("▶️ Executing query...")
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]

        cur.close()
        conn.close()
        print("✅ Query executed successfully, rows fetched:", len(rows))

        results = [dict(zip(colnames, row)) for row in rows]
        return {"statusCode": 200, "body": json.dumps(results, cls=CustomJSONEncoder)}

    except Exception as e:
        print("💥 ERROR in Lambda:", str(e))
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
##---------------------------------------------------------##
##              creating all the tables                    ##
##---------------------------------------------------------##
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 1. Support Staff
-- =====================================================
CREATE TABLE support_staff (
    staff_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    role TEXT,
    email TEXT UNIQUE,
    phone TEXT
);

-- =====================================================
-- 2. Programs
-- =====================================================
CREATE TABLE programs (
    program_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    program_name TEXT NOT NULL,
    description TEXT
);

-- =====================================================
-- 3. Phases
-- =====================================================
CREATE TABLE phases (
    phase_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phase_name TEXT NOT NULL,
    program_id UUID REFERENCES programs(program_id) ON DELETE CASCADE,
    order_number INT
);

-- =====================================================
-- 4. Weeks
-- =====================================================
CREATE TABLE weeks (
    week_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phase_id UUID REFERENCES phases(phase_id) ON DELETE CASCADE,
    week_number INT
);

-- =====================================================
-- 5. Days
-- =====================================================
CREATE TABLE days (
    day_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    week_id UUID REFERENCES weeks(week_id) ON DELETE CASCADE,
    day_number INT
);

-- =====================================================
-- 6. Exercises
-- =====================================================
CREATE TABLE exercises (
    exercise_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    day_id UUID REFERENCES days(day_id) ON DELETE CASCADE,
    exercise_name TEXT,
    description TEXT,
    sets INT,
    reps INT
);

-- =====================================================
-- 7. Diet Plans
-- =====================================================
CREATE TABLE diet_plans (
    diet_plan_id      UUID PRIMARY KEY,
    category          VARCHAR(50),
    diet_regime       VARCHAR(100),
    diet_lifestyle    VARCHAR(100),
    diet_goal         VARCHAR(100),
    diet_preference   VARCHAR(100),
    support_staff_id  VARCHAR(100),
    support_staff_name VARCHAR(100)
);

-- =====================================================
-- 8. Diet Plan Weeks
-- =====================================================
CREATE TABLE diet_plan_weeks (
    diet_week_id     UUID PRIMARY KEY,
    diet_plan_id     UUID NOT NULL,
    diet_week_number INT NOT NULL,
    FOREIGN KEY (diet_plan_id) REFERENCES diet_plans(diet_plan_id) ON DELETE CASCADE
);

-- =====================================================
-- 9. Diet Plan Days
-- =====================================================
CREATE TABLE diet_plan_days (
    diet_day_id    UUID PRIMARY KEY,
    diet_plan_id   UUID NOT NULL,
    diet_week_id   UUID NOT NULL,
    day_number     INT NOT NULL,
    FOREIGN KEY (diet_plan_id) REFERENCES diet_plans(diet_plan_id) ON DELETE CASCADE,
    FOREIGN KEY (diet_week_id) REFERENCES diet_plan_weeks(diet_week_id) ON DELETE CASCADE
);

-- =====================================================
-- 10. Meals
-- =====================================================
CREATE TABLE diet_plan_meals (
    meal_id       UUID PRIMARY KEY,
    diet_plan_id  UUID NOT NULL,
    diet_week_id  UUID NOT NULL,
    diet_day_id   UUID NOT NULL,
    meal_type     VARCHAR(50),    -- Breakfast, Lunch, Dinner, etc.
    meal_name     VARCHAR(200),
    calories      INT,
    fat           INT,
    carbs         INT,
    protein       INT,
    FOREIGN KEY (diet_plan_id) REFERENCES diet_plans(diet_plan_id) ON DELETE CASCADE,
    FOREIGN KEY (diet_week_id) REFERENCES diet_plan_weeks(diet_week_id) ON DELETE CASCADE,
    FOREIGN KEY (diet_day_id) REFERENCES diet_plan_days(diet_day_id) ON DELETE CASCADE
);

-- =====================================================
-- 11. Client
-- =====================================================
CREATE TABLE client (
    client_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT,
    diet_plan_id UUID REFERENCES diet_plans(diet_plan_id) ON DELETE SET NULL
);

-- =====================================================
-- 12. Customer Uploaded Meals
-- =====================================================
CREATE TABLE customer_uploaded_meals (
    upload_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES client(client_id) ON DELETE CASCADE,
    meal_id UUID REFERENCES meals(meal_id) ON DELETE CASCADE,
    notes TEXT
);

-- =====================================================
-- 13. Support Staff Assigned
-- =====================================================
CREATE TABLE support_staff_assigned (
    assignment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES client(client_id) ON DELETE CASCADE,
    staff_id UUID REFERENCES support_staff(staff_id) ON DELETE CASCADE
);

-- =====================================================
-- 14. Lifestyle
-- =====================================================
CREATE TABLE lifestyle (
    lifestyle_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES client(client_id) ON DELETE CASCADE,
    activity_level TEXT
);

-- =====================================================
-- 15. Client Activity
-- =====================================================
CREATE TABLE client_activity (
    activity_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES client(client_id) ON DELETE CASCADE,
    activity_description TEXT
);

-- =====================================================
-- 16. Exercise Feedback
-- =====================================================
CREATE TABLE exercise_feedback (
    feedback_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES client(client_id) ON DELETE CASCADE,
    exercise_id UUID REFERENCES exercises(exercise_id) ON DELETE CASCADE,
    feedback TEXT
);
##---------------------------------------------------------##
##                 sequence for tables                     ##
##---------------------------------------------------------##
support_staff → diet_plans → programs → phases → weeks → days → exercises → client → feedback/meals


##---------------------------------------------------------##
##                  Diet plan payload                      ##
##---------------------------------------------------------##
[
    {
        "table_name": "diet_plans",
        "data": {
            "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
            "category": "master",
            "diet_regime": "Plan 89",
            "diet_lifestyle": "Moderate Exercise",
            "diet_goal": "Muscle Gain",
            "diet_preference": "Veg without onion",
            "support_staff_id": "abcdefghijklmno",
            "support_staff_name": "Harshil"
        }
    },
    {
        "table_name": "diet_plan_weeks",
        "data": [
            {
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "7660d60c-5758-48dc-940f-0b035270215e",
                "diet_week_number": 1
            },
            {
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "369ef923-e624-440a-93ab-9ea07316a6ce",
                "diet_week_number": 2
            }
        ]
    },
    {
        "table_name": "diet_plan_days",
        "data": [
            {
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "7660d60c-5758-48dc-940f-0b035270215e",
                "diet_day_id": "1ec8a779-a02f-43c7-b66c-8b6f3e76f1f4",
                "day_number": 1
            },
            {
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "7660d60c-5758-48dc-940f-0b035270215e",
                "diet_day_id": "0c217c1a-c2c6-4b26-a15d-fd114646ed1a",
                "day_number": 2
            },
            {
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "7660d60c-5758-48dc-940f-0b035270215e",
                "diet_day_id": "03b5dda8-7535-4837-99b9-ba2025c884d9",
                "day_number": 3
            },
            {
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "7660d60c-5758-48dc-940f-0b035270215e",
                "diet_day_id": "e96e583b-a553-4910-b6e4-ffb445a5a86c",
                "day_number": 4
            },
            {
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "7660d60c-5758-48dc-940f-0b035270215e",
                "diet_day_id": "688ab454-72b2-482c-a01f-a654db195838",
                "day_number": 5
            },
            {
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "7660d60c-5758-48dc-940f-0b035270215e",
                "diet_day_id": "37ab770e-8b47-46e4-bc23-f3156f7f3b29",
                "day_number": 6
            },
            {
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "7660d60c-5758-48dc-940f-0b035270215e",
                "diet_day_id": "85c058c1-d17e-4d06-8184-ec927a1f6d67",
                "day_number": 7
            },
            {
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "369ef923-e624-440a-93ab-9ea07316a6ce",
                "diet_day_id": "c8ba4b3b-b961-416b-8ccc-32f607616692",
                "day_number": 1
            },
            {
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "369ef923-e624-440a-93ab-9ea07316a6ce",
                "diet_day_id": "4d87aef2-45a0-4835-a0f8-c99057bc4e64",
                "day_number": 2
            },
            {
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "369ef923-e624-440a-93ab-9ea07316a6ce",
                "diet_day_id": "4057665b-d355-42d8-8dee-2f2a118ab719",
                "day_number": 3
            },
            {
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "369ef923-e624-440a-93ab-9ea07316a6ce",
                "diet_day_id": "a06ce3cb-9d04-4681-9fbf-9c995c3eb2dd",
                "day_number": 4
            },
            {
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "369ef923-e624-440a-93ab-9ea07316a6ce",
                "diet_day_id": "7a6f2bbe-904f-403f-86fa-515cda1661d5",
                "day_number": 5
            },
            {
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "369ef923-e624-440a-93ab-9ea07316a6ce",
                "diet_day_id": "0785372f-da21-4ee8-9f46-e520e8a879b5",
                "day_number": 6
            },
            {
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "369ef923-e624-440a-93ab-9ea07316a6ce",
                "diet_day_id": "7e356d65-3fbb-43ed-98ca-e982732afd3b",
                "day_number": 7
            }
        ]
    },
    {
        "table_name": "diet_plan_meals",
        "data": [
            {
                "meal_id": "5b015d2a-0f34-42ce-ade3-ee2476567416",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "7660d60c-5758-48dc-940f-0b035270215e",
                "diet_day_id": "1ec8a779-a02f-43c7-b66c-8b6f3e76f1f4",
                "meal_type": "Lunch",
                "meal_name": "Grilled Chicken Salad",
                "calories": 450,
                "fat": 15,
                "carbs": 20,
                "protein": 40
            },

            {
                "meal_id": "e33ad2e5-31de-4f82-b9b4-f70d296628cd",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "7660d60c-5758-48dc-940f-0b035270215e",
                "diet_day_id": "1ec8a779-a02f-43c7-b66c-8b6f3e76f1f4",
                "meal_type": "Dinner",
                "meal_name": "Quinoa & Veg Stir Fry",
                "calories": 380,
                "fat": 10,
                "carbs": 50,
                "protein": 12
            },
            {
                "meal_id": "0e110a48-bd07-4a48-926f-a35aa4807839",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "7660d60c-5758-48dc-940f-0b035270215e",
                "diet_day_id": "1ec8a779-a02f-43c7-b66c-8b6f3e76f1f4",
                "meal_type": "Lunch",
                "meal_name": "Turkey Wrap",
                "calories": 420,
                "fat": 14,
                "carbs": 35,
                "protein": 30
            },
            {
                "meal_id": "be8d2705-f298-4d81-b262-52210b77c0e3",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "7660d60c-5758-48dc-940f-0b035270215e",
                "diet_day_id": "0c217c1a-c2c6-4b26-a15d-fd114646ed1a",
                "meal_type": "Breakfast",
                "meal_name": "Oatmeal with Berries",
                "calories": 320,
                "fat": 6,
                "carbs": 54,
                "protein": 10
            },
            {
                "meal_id": "ceea4b75-522b-4a1e-8c8d-d0606ca809f6",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "7660d60c-5758-48dc-940f-0b035270215e",
                "diet_day_id": "03b5dda8-7535-4837-99b9-ba2025c884d9",
                "meal_type": "Lunch",
                "meal_name": "Grilled Chicken Salad",
                "calories": 450,
                "fat": 15,
                "carbs": 20,
                "protein": 40
            },
            {
                "meal_id": "324bb0b8-b85b-4397-9366-a6c71967743e",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "7660d60c-5758-48dc-940f-0b035270215e",
                "diet_day_id": "03b5dda8-7535-4837-99b9-ba2025c884d9",
                "meal_type": "Dinner",
                "meal_name": "Quinoa & Veg Stir Fry",
                "calories": 380,
                "fat": 10,
                "carbs": 50,
                "protein": 12
            },
            {
                "meal_id": "86631784-42e5-4306-b063-ce1d4c691c57",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "7660d60c-5758-48dc-940f-0b035270215e",
                "diet_day_id": "03b5dda8-7535-4837-99b9-ba2025c884d9",
                "meal_type": "Breakfast",
                "meal_name": "Avocado Toast with Egg",
                "calories": 300,
                "fat": 18,
                "carbs": 26,
                "protein": 12
            },
            {
                "meal_id": "afc6db25-b30e-4fd3-8f74-d92939a40a66",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "7660d60c-5758-48dc-940f-0b035270215e",
                "diet_day_id": "03b5dda8-7535-4837-99b9-ba2025c884d9",
                "meal_type": "Lunch",
                "meal_name": "Turkey Wrap",
                "calories": 420,
                "fat": 14,
                "carbs": 35,
                "protein": 30
            },
            {
                "meal_id": "0e0936af-574b-43ff-9d4f-d26bbb6367af",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "7660d60c-5758-48dc-940f-0b035270215e",
                "diet_day_id": "688ab454-72b2-482c-a01f-a654db195838",
                "meal_type": "Dinner",
                "meal_name": "Sweet Potato & Black Bean Bowl",
                "calories": 480,
                "fat": 16,
                "carbs": 60,
                "protein": 18
            },
            {
                "meal_id": "dd213929-cd76-4e1f-9e46-c8ec004a707a",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "7660d60c-5758-48dc-940f-0b035270215e",
                "diet_day_id": "688ab454-72b2-482c-a01f-a654db195838",
                "meal_type": "Breakfast",
                "meal_name": "Cottage Cheese Bowl",
                "calories": 280,
                "fat": 10,
                "carbs": 12,
                "protein": 22
            },
            {
                "meal_id": "36efd70e-e3b9-487e-b468-e02ae73c60b9",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "7660d60c-5758-48dc-940f-0b035270215e",
                "diet_day_id": "688ab454-72b2-482c-a01f-a654db195838",
                "meal_type": "Lunch",
                "meal_name": "Zucchini Noodles with Pesto",
                "calories": 220,
                "fat": 14,
                "carbs": 10,
                "protein": 8
            },
            {
                "meal_id": "de98d5ad-9e80-4e37-9b07-32c94402bd1c",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "369ef923-e624-440a-93ab-9ea07316a6ce",
                "diet_day_id": "c8ba4b3b-b961-416b-8ccc-32f607616692",
                "meal_type": "Breakfast",
                "meal_name": "Oatmeal with Berries",
                "calories": 320,
                "fat": 6,
                "carbs": 54,
                "protein": 10
            },
            {
                "meal_id": "ef8df67b-993d-4b5e-8f60-b16d70dca73b",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "369ef923-e624-440a-93ab-9ea07316a6ce",
                "diet_day_id": "c8ba4b3b-b961-416b-8ccc-32f607616692",
                "meal_type": "Lunch",
                "meal_name": "Grilled Chicken Salad",
                "calories": 450,
                "fat": 15,
                "carbs": 20,
                "protein": 40
            },
            {
                "meal_id": "ef14faed-01d9-4748-9a25-089d1f2f576f",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "369ef923-e624-440a-93ab-9ea07316a6ce",
                "diet_day_id": "c8ba4b3b-b961-416b-8ccc-32f607616692",
                "meal_type": "Breakfast",
                "meal_name": "Avocado Toast with Egg",
                "calories": 300,
                "fat": 18,
                "carbs": 26,
                "protein": 12
            },
            {
                "meal_id": "e969f8a9-27dc-4afb-b31d-bd81ebe078fa",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "369ef923-e624-440a-93ab-9ea07316a6ce",
                "diet_day_id": "4d87aef2-45a0-4835-a0f8-c99057bc4e64",
                "meal_type": "Lunch",
                "meal_name": "Grilled Chicken Salad",
                "calories": 450,
                "fat": 15,
                "carbs": 20,
                "protein": 40
            },
            {
                "meal_id": "70deb62c-5138-4f40-a325-92bb585832e2",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "369ef923-e624-440a-93ab-9ea07316a6ce",
                "diet_day_id": "4d87aef2-45a0-4835-a0f8-c99057bc4e64",
                "meal_type": "Dinner",
                "meal_name": "Quinoa & Veg Stir Fry",
                "calories": 380,
                "fat": 10,
                "carbs": 50,
                "protein": 12
            },
            {
                "meal_id": "dc82229b-cc87-411f-870a-e1610742d500",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "369ef923-e624-440a-93ab-9ea07316a6ce",
                "diet_day_id": "4d87aef2-45a0-4835-a0f8-c99057bc4e64",
                "meal_type": "Breakfast",
                "meal_name": "Avocado Toast with Egg",
                "calories": 300,
                "fat": 18,
                "carbs": 26,
                "protein": 12
            },
            {
                "meal_id": "ae7bb05e-f012-4b7f-800b-fe72da657ead",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "369ef923-e624-440a-93ab-9ea07316a6ce",
                "diet_day_id": "4057665b-d355-42d8-8dee-2f2a118ab719",
                "meal_type": "Breakfast",
                "meal_name": "Oatmeal with Berries",
                "calories": 320,
                "fat": 6,
                "carbs": 54,
                "protein": 10
            },
            {
                "meal_id": "998896ae-2df2-4fb0-bc02-806dc3f60d09",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "369ef923-e624-440a-93ab-9ea07316a6ce",
                "diet_day_id": "4057665b-d355-42d8-8dee-2f2a118ab719",
                "meal_type": "Lunch",
                "meal_name": "Grilled Chicken Salad",
                "calories": 450,
                "fat": 15,
                "carbs": 20,
                "protein": 40
            },
            {
                "meal_id": "dbd62135-049c-4ff5-9d21-29327e6bbd3e",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "369ef923-e624-440a-93ab-9ea07316a6ce",
                "diet_day_id": "4057665b-d355-42d8-8dee-2f2a118ab719",
                "meal_type": "Dinner",
                "meal_name": "Quinoa & Veg Stir Fry",
                "calories": 380,
                "fat": 10,
                "carbs": 50,
                "protein": 12
            },
            {
                "meal_id": "eb9af69c-0eb9-4439-a61a-12ca895aaa28",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "369ef923-e624-440a-93ab-9ea07316a6ce",
                "diet_day_id": "4057665b-d355-42d8-8dee-2f2a118ab719",
                "meal_type": "Breakfast",
                "meal_name": "Avocado Toast with Egg",
                "calories": 300,
                "fat": 18,
                "carbs": 26,
                "protein": 12
            },
            {
                "meal_id": "1ad4d108-ecec-49df-91f2-37dbf6480d66",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "369ef923-e624-440a-93ab-9ea07316a6ce",
                "diet_day_id": "0785372f-da21-4ee8-9f46-e520e8a879b5",
                "meal_type": "Lunch",
                "meal_name": "Grilled Chicken Salad",
                "calories": 450,
                "fat": 15,
                "carbs": 20,
                "protein": 40
            },
            {
                "meal_id": "b4cb9b1d-f1ab-46fc-88c0-86b65a4cb0f2",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "369ef923-e624-440a-93ab-9ea07316a6ce",
                "diet_day_id": "0785372f-da21-4ee8-9f46-e520e8a879b5",
                "meal_type": "Dinner",
                "meal_name": "Quinoa & Veg Stir Fry",
                "calories": 380,
                "fat": 10,
                "carbs": 50,
                "protein": 12
            },
            {
                "meal_id": "fc239503-72fe-417d-a6bf-888ff90064c2",
                "diet_plan_id": "d1bca9af-23bb-4e20-8b45-9972aff6fe0e",
                "diet_week_id": "369ef923-e624-440a-93ab-9ea07316a6ce",
                "diet_day_id": "0785372f-da21-4ee8-9f46-e520e8a879b5",
                "meal_type": "Breakfast",
                "meal_name": "Avocado Toast with Egg",
                "calories": 300,
                "fat": 18,
                "carbs": 26,
                "protein": 12
            }
        ]
    }
]
##-------------------------------------------------##
##               push onboarding question          ##
##-------------------------------------------------##
import json
import psycopg2
import uuid
import traceback

def lambda_handler(event, context):
    try:
        print("📥 Incoming event:", event)

        # Parse request body
        body = json.loads(event.get("body", "[]"))
        print("📦 Parsed body:", body)

        if isinstance(body, dict):
            inserts = [body]
        elif isinstance(body, list):
            inserts = body
        else:
            error_msg = "Invalid payload format. Must be object or array."
            print("❌ Error:", error_msg)
            return {
                "statusCode": 400,
                "body": json.dumps({"error": error_msg})
            }

        # Database connection details
        creds = {
            "host": "granimals-dev-cluster-1.cr82g6co4rta.ap-south-1.rds.amazonaws.com",
            "port": 5432,
            "dbname": "granimalsdev",
            "username": "granimals_rds",
            "password": "rdsSecret#1"
        }

        print("🔗 Connecting to PostgreSQL...")
        conn = psycopg2.connect(
            host=creds['host'],
            port=creds['port'],
            dbname=creds['dbname'],
            user=creds['username'],
            password=creds['password']
        )
        conn.autocommit = True  # ✅ Run each statement in its own transaction
        cur = conn.cursor()
        print("✅ Database connection established")

        results = []

        for item in inserts:
            table_name = item.get("table_name")
            data = item.get("data", {})

            print(f"\n➡️ Processing insert for table: {table_name}")

            if not table_name or not data:
                error_msg = "Missing table_name or data"
                print(f"❌ Error for {table_name}: {error_msg}")
                results.append({
                    "table": table_name or "unknown",
                    "status": "failed",
                    "error": error_msg
                })
                continue

            # Normalize → always a list of rows
            rows = data if isinstance(data, list) else [data]

            for row in rows:
                try:
                    # ✅ UUID validation
                    for key, value in row.items():
                        if (
                            "id" in key.lower()
                            and isinstance(value, str)
                            and len(value) == 36
                            and value.count("-") == 4
                        ):
                            try:
                                row[key] = str(uuid.UUID(value))
                            except ValueError:
                                error_msg = f"Invalid UUID format for '{key}'"
                                print(f"❌ {error_msg}")
                                results.append({
                                    "table": table_name,
                                    "status": "failed",
                                    "error": error_msg
                                })
                                raise  # Skip insert for this row

                    # Build insert query
                    fields = ", ".join(row.keys())
                    placeholders = ", ".join(["%s"] * len(row))
                    values = list(row.values())
                    query = f"INSERT INTO {table_name} ({fields}) VALUES ({placeholders})"

                    print(f"📝 Executing query: {query} with values {values}")
                    cur.execute(query, values)

                    print(f"✅ Insert successful for table {table_name}")
                    results.append({"table": table_name, "status": "success"})

                except Exception as e:
                    error_msg = str(e)
                    print(f"❌ Insert failed for {table_name}: {error_msg}")
                    print("🔍 Traceback:", traceback.format_exc())
                    results.append({
                        "table": table_name,
                        "status": "failed",
                        "error": error_msg
                    })

        cur.close()
        conn.close()
        print("🔒 Connection closed")

        return {
            "statusCode": 200,
            "body": json.dumps({"results": results})
        }

    except Exception as e:
        error_msg = str(e)
        print("🔥 Fatal error in lambda_handler:", error_msg)
        print("🔍 Traceback:", traceback.format_exc())
        return {
            "statusCode": 500,
            "body": json.dumps({"error": error_msg})
        }
##-------------------------------------------------##
##       Payload push onboarding question          ##
##-------------------------------------------------##
{
  "client_id": "d8f27e36-7a4f-4c6f-b60c-fb9c2a2b6c1e",
  "gender_identity": "male",
  "birthdate": "1995-06-21",
  "height": 175.5,
  "height_unit": "cm",
  "height_accuracy": "self_reported",
  "weight": 72.4,
  "weight_unit": "kg",
  "preferred_workout_time": "Morning",
  "sleep_time": "23:30:00",
  "wake_up_time": "06:45:00",
  "breakfast_time": "08:00:00",
  "lunch_time": "13:00:00",
  "dinner_time": "20:00:00",
  "snack_frequency": "Often"
}
##-------------------------------------------------##
##               pull onboarding question          ##
##-------------------------------------------------##
import json
import psycopg2
import os
import traceback

def lambda_handler(event, context):
    try:
        print("📥 Incoming event:", event)

        # Handle API Gateway or direct invoke
        body = json.loads(event.get("body", "{}")) if isinstance(event, dict) else event
        client_id = body.get("client_id")

        if not client_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "client_id is required"})
            }

        # DB connection
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST", "granimals-dev-cluster-1.cr82g6co4rta.ap-south-1.rds.amazonaws.com"),
            port=int(os.environ.get("DB_PORT", 5432)),
            dbname=os.environ.get("DB_NAME", "granimalsdev"),
            user=os.environ.get("DB_USER", "granimals_rds"),
            password=os.environ.get("DB_PASS", "rdsSecret#1")
        )
        cur = conn.cursor()

        query = """
            SELECT id, client_id, gender_identity, birthdate, height, height_unit,
                   height_accuracy, weight, weight_unit, preferred_workout_time,
                   sleep_time, wake_up_time, breakfast_time, lunch_time, dinner_time,
                   snack_frequency, creation_date_time
            FROM onboarding_questionnaire
            WHERE client_id = %s
            ORDER BY creation_date_time DESC
            LIMIT 1
        """

        cur.execute(query, (client_id,))
        row = cur.fetchone()

        cur.close()
        conn.close()

        if not row:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "No onboarding responses found for this client_id"})
            }

        # Convert row → dict
        col_names = [
            "id", "client_id", "gender_identity", "birthdate", "height", "height_unit",
            "height_accuracy", "weight", "weight_unit", "preferred_workout_time",
            "sleep_time", "wake_up_time", "breakfast_time", "lunch_time", "dinner_time",
            "snack_frequency", "creation_date_time"
        ]
        result = dict(zip(col_names, row))

        return {
            "statusCode": 200,
            "body": json.dumps(result, default=str)  # default=str handles DATE/TIME
        }

    except Exception as e:
        error_msg = str(e)
        print("🔥 Fatal error in lambda_handler:", error_msg)
        print("🔍 Traceback:", traceback.format_exc())
        return {
            "statusCode": 500,
            "body": json.dumps({"error": error_msg})
        }

##------------------------------------------------------------##
##                    chatgpt_integration                     ##
##------------------------------------------------------------##
import json
import os
import base64
import boto3
import logging
import urllib.request

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Cache secrets for warm starts
_cached_api_key = None

def get_openai_key():
    global _cached_api_key
    if _cached_api_key:
        return _cached_api_key

    secret_name = os.environ.get("OPENAI_SECRET_NAME", "openai_key")
    region = os.environ.get("AWS_REGION", "ap-south-1")

    client = boto3.client("secretsmanager", region_name=region)
    resp = client.get_secret_value(SecretId=secret_name)

    if "SecretString" in resp:
        val = resp["SecretString"]
        try:
            data = json.loads(val)
            _cached_api_key = (
                data.get("OPENAI_API_KEY")
                or data.get("openai_api_key")
                or data.get("api_key")
            )
        except Exception:
            _cached_api_key = val
    else:
        _cached_api_key = base64.b64decode(resp["SecretBinary"]).decode("utf-8")

    return _cached_api_key

def safe_json_extract(content: str):
    """Extract valid JSON even if wrapped in markdown fences."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Strip markdown ```json fences if present
        if content.strip().startswith("```"):
            cleaned = "\n".join(
                line for line in content.splitlines()
                if not line.strip().startswith("```")
            )
            try:
                return json.loads(cleaned)
            except Exception:
                pass
        # Last fallback → wrap into result
        return {"result": content, "details": {"warning": "Model did not return strict JSON"}}

def call_chatgpt(prompt, inputs):
    """
    Generic HTTPS call to OpenAI Chat Completions/Responses style.
    """
    api_key = get_openai_key()
    api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    url = f"{api_base}/chat/completions"
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a strict JSON API."},
            {
                "role": "user",
                "content": (
                    f"Inputs:\n"
                    f"input1: {inputs['input1']}\n"
                    f"input2: {inputs['input2']}\n"
                    f"input3: {inputs['input3']}\n"
                    f"Task: {prompt}\n"
                ),
            },
        ],
        "temperature": 0.2,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8")
        data = json.loads(raw)
        content = data["choices"][0]["message"]["content"]
        return safe_json_extract(content)

def parse_event(event):
    if event.get("isBase64Encoded"):
        body = base64.b64decode(event.get("body") or "").decode("utf-8")
    else:
        body = event.get("body") or ""
    try:
        return json.loads(body)
    except Exception:
        return {}

def response(status, body, origin):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Headers": "content-type,authorization",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
        },
        "body": json.dumps(body),
    }

def lambda_handler(event, context):
    logger.info({"event": event.get("requestContext", {})})
    origin = os.environ.get("FRONTEND_ORIGIN", "*")

    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return response(200, {"ok": True}, origin)

    payload = parse_event(event)
    input1 = payload.get("input1")
    input2 = payload.get("input2")
    input3 = payload.get("input3")

    missing = [k for k, v in {"input1": input1, "input2": input2, "input3": input3}.items() if v is None]
    if missing:
        return response(400, {"error": f"Missing fields: {', '.join(missing)}"}, origin)

    # Nutrition prompt
    prompt = (
        "You are a nutrition assistant for Granimals. "
        "Given a food item and its quantity, return the estimated nutritional values "
        "in JSON format only. Do not include any extra fields.\n\n"
        f"Food item: {input1}\n"
        f"Quantity: {input2} {input3}\n\n"
        "Respond strictly as:\n"
        "{\n"
        "  \"calories\": <number>,\n"
        "  \"carbs\": <number>,\n"
        "  \"fats\": <number>,\n"
        "  \"proteins\": <number>,\n"
        "  \"fibre\": <number>\n"
        "}"
    )

    try:
        result = call_chatgpt(prompt, {"input1": input1, "input2": input2, "input3": input3})
        return response(200, result, origin)
    except Exception as e:
        logger.exception("chatgpt_call_failed")
        return response(502, {"ok": False, "error": str(e)}, origin)
