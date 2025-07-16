# Augur Chatbot

This project is a database chat assistant for querying the [CHAOSS Augur](https://chaoss.github.io/augur/) open source software community metrics platform. Augur can collect and organizes GitHub data for thousands of repositories to help stakeholders understand contributor behavior, project health, and community trends.
This chatbot enhances connects with Augur by enabling users to ask questions in natural language and receive accurate, SQL-grounded answers powered by an LLM. It's designed for people who want quick insights into open source projects or company-level impact without needing to write SQL.

---
## Requirements
- Python 3.10+
- [Ollama](https://ollama.com/) (for running LLaMA models locally)
- [Podman](https://podman.io/) (or Docker)
- A running Augur PostgreSQL database and credentials

## Setup
To get started:
1. **Clone the repo**
```bash
   git clone https://github.com/redhat-et/augur-chatbot.git
   cd augur-chatbot
```
2. **Create a virtual environment (recommended)**
```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
```
3. **Install Dependencies**
Install dependencies from pyproject.toml:
```bash
  pip install -e .
```
4. **Create a .env file with your Augur Database credentials**
You can either:
Connect to an existing Augur instance (e.g., with replica data), or
Spin up a local instance and populate it with repository data of your choosing.

Create a .env file in the root directory by copying the example file. Then fill in your database credentials:
```bash
  cp .env.example .env
```

5. **Run LlamaStack and Ollama locally**
```bash
  make setup_local
```
Or, optionally plug in your own model url into the Makefile

6. **Register the MCP tool server**
```bash
  python register_mcp.py
```

7. **Start the MCP SQL Server**
```bash
  make run_ui
```

8. **Run the Streamlit UI**
```bash
   streamlit ui.py run
```
Once running, the chatbot can answer a wide range of schema-aware questions about the Augur database. [ADD SAMPLE QUERIES]

Under the hood, the tool uses a hybrid tool-calling approach with a customized schema retriever and Model Context Protocol (MCP) execution layer, ensuring SQL queries are grounded in the actual structure of your Augur instance.
   
