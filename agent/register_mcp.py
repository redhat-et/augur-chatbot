from llama_stack_client import LlamaStackClient

client = LlamaStackClient(base_url="http://localhost:8321")

client.toolgroups.register(
    toolgroup_id="mcp::postgres",
    provider_id="model-context-protocol",
    mcp_endpoint={"uri": "http://host.containers.internal:8000/sse"},
)

print("✅ Registered mcp::postgres via host.containers.internal:8000")

client.toolgroups.register(
    toolgroup_id="mcp::sql",
    provider_id="model-context-protocol",
    mcp_endpoint={"uri": "http://host.containers.internal:9001/sse"},
)

print("✅ Registered custom MCP toolgroup at port 9001")

client.toolgroups.register(
    toolgroup_id="mcp::execute",
    provider_id="model-context-protocol",
    mcp_endpoint={"uri": "http://host.containers.internal:9002/sse"},
)

print("✅ Registered custom MCP toolgroup at port 9002")