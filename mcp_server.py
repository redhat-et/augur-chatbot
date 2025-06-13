# tool_server.py

from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
import psycopg2
import os
from dotenv import load_dotenv

# Load database URI from .env
load_dotenv()
DATABASE_URI = os.getenv("DATABASE_URI")

app = FastAPI()
mcp = FastMCP(app, toolgroup_id="mcp::describe_schema")

# Tool: describe_schema
@mcp.tool("describe_schema", description="Returns the full schema of the connected PostgreSQL database.")
def describe_schema() -> str:
    conn = psycopg2.connect(DATABASE_URI)
    cur = conn.cursor()

    cur.execute("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    schema_dict = {}
    for table, column, dtype in rows:
        schema_dict.setdefault(table, []).append(f"{column} ({dtype})")

    # Format schema as a readable string
    return "\n".join(
        f"- {table}: " + ", ".join(columns)
        for table, columns in schema_dict.items()
    )
