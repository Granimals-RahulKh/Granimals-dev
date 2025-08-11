import psycopg2
import json
import os

def lambda_handler(event, context):
    body = json.loads(event['body'])
    table_name = body['table']
    data = body['data']  # dict of field: value

    conn = psycopg2.connect(
        host=os.environ['DB_HOST'],
        port=5432,
        dbname=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD']
    )
    cursor = conn.cursor()

    # Build SQL dynamically based on provided fields
    fields = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    values = tuple(data.values())

    sql = f"INSERT INTO {table_name} ({fields}) VALUES ({placeholders})"
    cursor.execute(sql, values)

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Data pushed successfully!"})
    }
