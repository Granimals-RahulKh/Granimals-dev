import boto3
import json
import os
import psycopg2
import traceback

def lambda_handler(event, context):
    try:
        method = event.get("httpMethod", "POST")
        print(f"HTTP Method: {method}")

        creds = {
            "host": "granimals-dev-cluster-1.cr82g6co4rta.ap-south-1.rds.amazonaws.com",
            "port": 5432,
            "dbname": "granimalsdev",
            "username": "granimals_rds",
            "password": "rdsSecret#1"
        }

        conn = psycopg2.connect(
            host=creds['host'],
            port=creds['port'],
            dbname=creds['dbname'],
            user=creds['username'],
            password=creds['password']
        )
        cursor = conn.cursor()

        if method == "POST":
            # --- PUSH mode ---
            body = json.loads(event.get('body', '{}'))
            if 'diet_plan_id' in body:
                insert_diet_plan(cursor, body)
                conn.commit()
                result = {"message": "Data inserted successfully"}
            else:
                result = {"error": "No diet_plan_id found in body"}

        elif method == "GET":
            # --- PULL mode ---
            params = event.get("queryStringParameters") or {}
            diet_plan_id = params.get("diet_plan_id")
            if not diet_plan_id:
                result = {"error": "diet_plan_id query parameter is required"}
            else:
                result = fetch_diet_plan(cursor, diet_plan_id)

        cursor.close()
        conn.close()

        return {
            "statusCode": 200,
            "body": json.dumps(result)
        }

    except Exception as e:
        traceback.print_exc()
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

# ------------------------
# INSERT Functions (Push)
# ------------------------
def insert_diet_plan(cursor, data):
    cursor.execute("""
        INSERT INTO diet_plans (diet_plan_id, category, support_staff_id)
        VALUES (%s, %s, %s)
    """, (data['diet_plan_id'], data['category'], data['support_staff_id']))

    for week in data.get('weeks', []):
        insert_diet_week(cursor, data['diet_plan_id'], week)

def insert_diet_week(cursor, diet_plan_id, week):
    cursor.execute("""
        INSERT INTO diet_weeks (diet_week_id, diet_plan_id, week_number)
        VALUES (%s, %s, %s)
    """, (week['diet_week_id'], diet_plan_id, week['week_number']))

    for day in week.get('days', []):
        insert_diet_day(cursor, week['diet_week_id'], day)

def insert_diet_day(cursor, diet_week_id, day):
    cursor.execute("""
        INSERT INTO diet_days (diet_day_id, diet_week_id, diet_day_name, date_assigned)
        VALUES (%s, %s, %s, %s)
    """, (day['diet_day_id'], diet_week_id, day['diet_day_name'], day['date_assigned']))

    for meal in day.get('meals', []):
        insert_diet_meal(cursor, day['diet_day_id'], meal)

def insert_diet_meal(cursor, diet_day_id, meal):
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

# ------------------------
# FETCH Function (Pull)
# ------------------------
def fetch_diet_plan(cursor, diet_plan_id):
    # Get plan
    cursor.execute("""
        SELECT diet_plan_id, category, support_staff_id
        FROM diet_plans
        WHERE diet_plan_id = %s
    """, (diet_plan_id,))
    plan = cursor.fetchone()
    if not plan:
        return {"error": "Diet plan not found"}

    plan_dict = {
        "diet_plan_id": plan[0],
        "category": plan[1],
        "support_staff_id": plan[2],
        "weeks": []
    }

    # Get weeks
    cursor.execute("""
        SELECT diet_week_id, week_number
        FROM diet_weeks
        WHERE diet_plan_id = %s
    """, (diet_plan_id,))
    weeks = cursor.fetchall()

    for week_id, week_num in weeks:
        week_dict = {
            "diet_week_id": week_id,
            "week_number": week_num,
            "days": []
        }

        # Get days
        cursor.execute("""
            SELECT diet_day_id, diet_day_name, date_assigned
            FROM diet_days
            WHERE diet_week_id = %s
        """, (week_id,))
        days = cursor.fetchall()

        for day_id, day_name, date_assigned in days:
            day_dict = {
                "diet_day_id": day_id,
                "diet_day_name": day_name,
                "date_assigned": date_assigned.isoformat() if date_assigned else None,
                "meals": []
            }

            # Get meals
            cursor.execute("""
                SELECT meal_type, meal_id, meal_name,
                       calories, proteins, fibers, fats,
                       time_of_meal, status, notes
                FROM diet_meals
                WHERE diet_day_id = %s
            """, (day_id,))
            meals = cursor.fetchall()

            for m in meals:
                meal_dict = {
                    "meal_type": m[0],
                    "meal_id": m[1],
                    "meal_name": m[2],
                    "calories": m[3],
                    "proteins": m[4],
                    "fibers": m[5],
                    "fats": m[6],
                    "time_of_meal": m[7],
                    "status": m[8],
                    "notes": json.loads(m[9]) if m[9] else []
                }
                day_dict["meals"].append(meal_dict)

            week_dict["days"].append(day_dict)

        plan_dict["weeks"].append(week_dict)

    return plan_dict
