from mcp.server.fastmcp import FastMCP
mcp = FastMCP("sql")

import psycopg2
import os

def execute_sql(sql: str) -> list[dict]:
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("AUGUR_DB", "augur"),
            user=os.getenv("AUGUR_USER", "user"),
            password=os.getenv("AUGUR_PASSWORD", "pass"),
            host=os.getenv("AUGUR_HOST", "localhost"),
            port=os.getenv("AUGUR_PORT", "port"),
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
        if cursor: cursor.close()
        if conn: conn.close()


@mcp.tool()
def get_augur_core_schema() -> str:
    """
    Returns a summary of the key tables used by this assistant.
    """
    return execute_sql("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'augur_data'
          AND table_name IN (
              'repo', 'contributors', 'commits',
              'contributor_affiliations', 'pull_request_reviewers'
          )
        ORDER BY table_name, ordinal_position
    """)

# Tool 1a: get contributor info by repo
@mcp.tool()
def get_contributor_contact_info(repo_name: str) -> list[dict]:
    """
    Returns contributor contact info (name and email) for a given repo.
    """
    sql = f"""
        SELECT DISTINCT c.cntrb_full_name, c.cntrb_email
        FROM augur_data.commits cm
        JOIN augur_data.repo r ON cm.repo_id = r.repo_id
        JOIN augur_data.contributors c ON cm.cmt_ght_author_id = c.cntrb_id
        WHERE r.repo_name = '{repo_name}'
        LIMIT 50
    """
    return execute_sql(sql)

# Tool 1b: get contributor affiliation by repo
@mcp.tool()
def get_contributor_affiliations(repo_name: str, affiliation_keyword: str) -> list[dict]:
    """
    Returns contributor names and affiliations for a given repo filtered by affiliation keyword.
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

# Tool 2: Top Contributors
@mcp.tool()
def get_top_contributors(repo_name: str, limit: int = 10) -> list[dict]:
    sql = f"""
        SELECT c.cntrb_login, COUNT(*) as commit_count
        FROM augur_data.commits cm
        JOIN augur_data.repo r ON cm.repo_id = r.repo_id
        JOIN augur_data.contributors c ON cm.cmt_ght_author_id = c.cntrb_id
        WHERE r.repo_name = '{repo_name}'
        GROUP BY c.cntrb_login
        ORDER BY commit_count DESC
        LIMIT {limit}
    """
    return execute_sql(sql)

# Tool 3: PR Reviewers
@mcp.tool()
def get_pr_reviewers(repo_name: str) -> list[dict]:
    """
    Returns contributors who have reviewed PRs in the given repo.
    """
    sql = f"""
        SELECT DISTINCT c.cntrb_login
        FROM augur_data.pull_request_reviewers prr
        JOIN augur_data.repo r ON prr.repo_id = r.repo_id
        JOIN augur_data.contributors c ON prr.cntrb_id = c.cntrb_id
        WHERE r.repo_name = '{repo_name}'
        """
    return execute_sql(sql)

# Tool 4: Top Languages by Repo Group
@mcp.tool()
def get_top_languages_by_repo_name(repo_name: str, limit: int = 5) -> list[dict]:
    repo_name = repo_name.replace("'", "''")  # Escape single quotes
    sql = f"""
        SELECT rl.programming_language, COUNT(*) AS usage_count
        FROM augur_data.repo_labor rl
        JOIN augur_data.repo r ON rl.repo_id = r.repo_id
        WHERE r.repo_name = '{repo_name}' AND rl.programming_language IS NOT NULL
        GROUP BY rl.programming_language
        ORDER BY usage_count DESC
        LIMIT {limit}
    """
    return execute_sql(sql)

# Tool 5: Monthly Contributions (based on cmt_author_timestamp)
@mcp.tool()
def get_monthly_contributions(repo_name: str, month: int, year: int) -> int:
    """
    Returns the number of commits to a specific repository in a given month and year.
    Uses a timestamp range filter for better performance.
    """
    from calendar import monthrange
    from datetime import datetime

    # Get first and last day of the month
    start_date = f"{year}-{month:02d}-01"
    end_day = monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{end_day}"

    sql = f"""
        SELECT COUNT(*) as contribution_count
        FROM augur_data.commits cm
        JOIN augur_data.repo r ON cm.repo_id = r.repo_id
        WHERE r.repo_name = '{repo_name}'
          AND cm.cmt_author_timestamp >= '{start_date}'
          AND cm.cmt_author_timestamp < '{end_date}'::date + INTERVAL '1 day'
    """
    return execute_sql(sql)


@mcp.tool()
def describe_schema() -> str:
    """
    Returns a list of tables and their columns from the augur_data schema.
    """
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

    schema_dict = {}
    for table, column, dtype in rows:
        schema_dict.setdefault(table, []).append(f"{column} ({dtype})")

    schema_text = "\n".join(
        f"- {table}: " + ", ".join(columns)
        for table, columns in schema_dict.items()
    )
    return schema_text


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='sse')


app = mcp.sse_app