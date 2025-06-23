import psycopg2
import json
import os

def get_augur_schema():
    conn = psycopg2.connect(os.environ["DATABASE_URI"])
    cur = conn.cursor()

    cur.execute("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'augur_data'
        ORDER BY table_name, ordinal_position
    """)
    rows = cur.fetchall()

    cur.close()
    conn.close()

    schema = {}
    for table, column, dtype in rows:
        schema.setdefault(table, []).append(f"{column} ({dtype})")

    return schema

if __name__ == "__main__":
    schema = get_augur_schema()

    with open("augur_schema.json", "w") as f:
        json.dump(schema, f, indent=2)

    print("Saved schema to augur_schema.json")
