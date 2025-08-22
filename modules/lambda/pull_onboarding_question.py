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
