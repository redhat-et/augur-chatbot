run_mcp:
	uvicorn mcp_execute:app --host 0.0.0.0 --port 9002

setup_local:
	mkdir -p ~/.llama
	ollama run llama3.2:3b-instruct-fp16 --keepalive 160m &
	podman run -it -p 8321:8321 -v ~/.llama:/root/.llama:Z llamastack/distribution-ollama:0.2.9 \
	--port 8321 \
	--env INFERENCE_MODEL="llama3.2:3b-instruct-fp16" \
	--env OLLAMA_URL=http://host.containers.internal:11434