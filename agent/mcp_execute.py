from mcp.server.fastmcp import FastMCP
import psycopg2
import os

mcp = FastMCP("execute")

# Core SQL executor
def execute_sql(sql: str) -> list[dict]:
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("AUGUR_DB", "augur"),
            user=os.getenv("AUGUR_USER", "ssreeram"),
            password=os.getenv("AUGUR_PASSWORD", "OMi0uuch0Ibo"),
            host=os.getenv("AUGUR_HOST", "localhost"),
            port=os.getenv("AUGUR_PORT", "5411"),
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

# Tool 1: Get project-level info
'''
@mcp.tool()
def get_project_info(repo_name: str) -> dict:
    """
    Returns the repo_id, GitHub URL, and associated repo group for a given project name.
    Use this when you need metadata about a specific project.
    """
    sql = f"""
        SELECT 
            r.repo_id, 
            r.url AS github_url, 
            rg.rg_name AS repo_group
        FROM augur_data.repo r
        JOIN augur_data.repo_groups rg ON r.repo_group_id = rg.repo_group_id
        WHERE r.repo_name = '{repo_name}'
        LIMIT 1;
    """
    results = execute_sql(sql)
    return results[0] if results else {"error": "Project not found."}
    '''

# Tool 4: Generic SQL query execution
@mcp.tool()
def execute_query(sql: str) -> list[dict]:
    """
    Executes a raw SQL query against the augur_data schema.
    Use this for all analytics queries about a project.
    """
    return execute_sql(sql)


# Start the MCP server
if __name__ == "__main__":
    mcp.run(transport="sse")

app = mcp.sse_app
