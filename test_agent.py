from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.agent import Agent

client = LlamaStackClient(base_url="http://localhost:8321")

agent = Agent(
    client,
    model="meta-llama/Llama-3.2-3B-Instruct",
    instructions="You have tools for querying a live postgres database.",
    tools=["mcp::postgres"],
    tool_config={"tool_choice": "auto"},
)

print("✅ Agent initialized successfully")
