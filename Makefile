run_mcp:
	uvicorn mcp_execute:app --host 0.0.0.0 --port 9002

setup_local: pull_models
	mkdir -p ~/.llama
	podman run -it -p 8321:8321 -v ~/.llama:/root/.llama:Z llamastack/distribution-ollama:0.2.9 \
	--port 8321 \
	--env INFERENCE_MODEL="llama3.2:3b-instruct-fp16" \
	--env OLLAMA_URL=http://host.containers.internal:11434

pull_models:
	ollama pull nomic-embed-text
	ollama pull llama3.2:3b-instruct-fp16

# This is designed for the container-based workflow
register_mcp:
	EXECUTE_MCP_URI=http://mcp_execute:9002/sse uv run register_mcp.py