# start_mcp_with_augur_tools.py
import mcp_tools_augur

from postgres_mcp.server import run_server

if __name__ == "__main__":
    run_server(
        transport="sse",
        host="0.0.0.0",
        port=9001  # Match your llamastack toolgroup URI
    )
