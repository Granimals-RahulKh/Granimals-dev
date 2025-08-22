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
