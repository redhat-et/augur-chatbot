## Custom MCP server - connects to a postgres database and executes SQL

from mcp.server.fastmcp import FastMCP
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

mcp = FastMCP("execute")

# Core SQL executor
def execute_sql(sql: str) -> list[dict]:
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("AUGUR_DB", "augur"),
            user=os.getenv("AUGUR_USER", "your_db_user"),
            password=os.getenv("AUGUR_PASSWORD", "your_db_password"),
            host=os.getenv("AUGUR_HOST", "localhost"),
            port=os.getenv("AUGUR_PORT", "5432"),
)
        cursor = conn.cursor()
        cursor.execute("SET search_path TO augur_data;")
        cursor.execute(sql)
        colnames = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(colnames, row)) for row in rows]
    except Exception as e:
        return [{"error": str(e)}]
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

## MCP tool - works with core SQL executor
@mcp.tool()
def execute_query(sql: str) -> list[dict]:
    """
    Executes a raw SQL query against the augur_data schema.
    Use this for all analytics queries about a project.
    """
    return execute_sql(sql)


@mcp.tool()
def get_contributor_affiliations(repo_name: str, affiliation_keyword: str) -> list[dict]:
    """
    Retrieve affiliation details for contributors on a given repository, optionally filtered by company name or email domain.
    """
    sql = f"""
        SELECT DISTINCT c.cntrb_full_name, ca.ca_affiliation
        FROM augur_data.commits cm
        JOIN augur_data.repo r ON cm.repo_id = r.repo_id
        JOIN augur_data.contributors c ON cm.cmt_ght_author_id = c.cntrb_id
        JOIN augur_data.contributor_affiliations ca ON c.cntrb_company = ca.ca_affiliation
        WHERE r.repo_name = '{repo_name}' AND ca.ca_affiliation ILIKE '%{affiliation_keyword}%'
        LIMIT 50
    """
    return execute_sql(sql)


# Start the MCP server
if __name__ == "__main__":
    mcp.run(transport="sse")

app = mcp.sse_app
