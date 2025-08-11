import psycopg2
import json
import os

def lambda_handler(event, context):
    body = json.loads(event['body'])
    table_name = body['table']
    lookup_field = body['lookup_field']   # e.g. "id"
    lookup_value = body['lookup_value']   # e.g. 123

    conn = psycopg2.connect(
        host=os.environ['DB_HOST'],
        port=5432,
        dbname=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD']
    )
    cursor = conn.cursor()

    sql = f"SELECT * FROM {table_name} WHERE {lookup_field} = %s"
    cursor.execute(sql, (lookup_value,))
    rows = cursor.fetchall()

    colnames = [desc[0] for desc in cursor.description]
    result = [dict(zip(colnames, row)) for row in rows]

    cursor.close()
    conn.close()

    return {
        "statusCode": 200,
        "body": json.dumps({"data": result})
    }
