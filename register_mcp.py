## Code to register various MCP toolkits, depending on tool use

from llama_stack_client import LlamaStackClient
from dotenv import load_dotenv
import os
load_dotenv()

# Base URL for the local LlamaStack server. Defaults to localhost if BASE_URL is not set.
base_url = os.getenv("BASE_URL", "http://localhost:8321")
client = LlamaStackClient(base_url = base_url)

client.toolgroups.register(
    toolgroup_id="mcp::postgres",
    provider_id="model-context-protocol",
    mcp_endpoint={"uri": os.getenv("POSTGRES_MCP_URI")},
)

print("✅ Registered mcp::postgres via host.containers.internal:8000")

client.toolgroups.register(
    toolgroup_id="mcp::sql",
    provider_id="model-context-protocol",
    mcp_endpoint={"uri": os.getenv("SQL_MCP_URI")},
)

print("✅ Registered custom MCP toolgroup at port 9001")

client.toolgroups.register(
    toolgroup_id="mcp::execute",
    provider_id="model-context-protocol",
    mcp_endpoint={"uri": os.getenv("EXECUTE_MCP_URI")},
)

print("✅ Registered custom MCP toolgroup at port 9002")