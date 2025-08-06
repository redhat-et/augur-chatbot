## Manual Setup

This is an older, more manual version of the setup steps for getting the chatbot working with fewer containers.


To get started:
1. **Clone the repo**
```bash
git clone https://github.com/redhat-et/augur-chatbot.git
cd augur-chatbot
```
2. **Create a .env file with your Augur Database credentials**
run `uv sync` to pull down python dependencies. If you dont have the `uv` dependency management tool for python, make sure its installed.

3. **Create a .env file with your Augur Database credentials**
You can either:
Connect to an existing Augur instance (e.g., with replica data), or
Spin up a local instance and populate it with repository data of your choosing.

Create a .env file in the root directory by copying the example file. Then fill in your database credentials:
```bash
cp .env.example .env
```

5. **Pull the models**
To ensure the models are downloaded and ready to go, run the following commands:
```
ollama pull nomic-embed-text
ollama pull llama3.2:3b-instruct-fp16
```
This will require ~ 7GB of free space on your machine.

6. **Start your local model server**
In a separate terminal, run
```bash
ollama serve
```
This will start a model server for your local ollama models that should remain running.

If you are using your own, externally hosted model url, you can skip this step.

7. **Run LlamaStack and Ollama locally**
```bash
make setup_local
```
Or, optionally plug in your own model url into the Makefile

8. **Register the MCP tool server**
```bash
uv run register_mcp.py
```

9. **Start the MCP SQL Server**
```bash
make run_mcp
```
10. **Run the Streamlit UI**
```bash
uv run streamlit run ui.py
```