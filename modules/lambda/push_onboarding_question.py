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
