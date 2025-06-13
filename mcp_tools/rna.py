# llama-stack-demos-main/mcp_tools/rna_tools.py

from mcp_sdk.tool import tool
import psycopg2

@tool(name="query_rna_by_type", description="Return RNA rows for a given RNA type")
def query_rna_by_type(rna_type: str) -> list:
    conn = psycopg2.connect(
        "host='hh-pgsql-public.ebi.ac.uk' dbname='pfmegrnargs' user='reader' password='NWDMCE5xdipIjRrp'"
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM rna WHERE rna_type = %s LIMIT 5", (rna_type,))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results
