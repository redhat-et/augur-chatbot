# tools.py or main.py inside postgres-mcp

from mcp_tools import tool  # from postgres-mcp's mcp_tools wrapper
import psycopg2

# Define connection
conn = psycopg2.connect(
    dbname="pfmegrnargs",
    user="reader",
    password="pfmegrnargs",
    host="hh-pgsql-public.ebi.ac.uk",  # usually "host.docker.internal" or "localhost"
    port="5432"
)
cur = conn.cursor()

@tool()
def list_tables() -> list[str]:
    """List all tables in the public schema."""
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    return [row[0] for row in cur.fetchall()]

@tool()
def describe_table(table_name: str) -> list[dict]:
    """Get column names and types for a specific table."""
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = %s
    """, (table_name,))
    return [{"column": name, "type": dtype} for name, dtype in cur.fetchall()]
