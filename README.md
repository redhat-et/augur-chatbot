# Augur Chatbot

This project is a database chat assistant for querying the [CHAOSS Augur](https://chaoss.github.io/augur/) open source software community metrics platform. Augur can collect and organizes GitHub data for thousands of repositories to help stakeholders understand contributor behavior, project health, and community trends.
This chatbot enhances connects with Augur by enabling users to ask questions in natural language and receive accurate, SQL-grounded answers powered by an LLM. It's designed for people who want quick insights into open source projects or company-level impact without needing to write SQL.

---

## Setup
To get started:
1. **Clone the repo**
```bash
   git clone https://github.com/redhat-et/augur-chatbot.git
   cd augur-chatbot
```
2. **Setup the environment**
```bash
  make setup_local
```
3. **Ensure your Augur database is running**
You can either:
Connect to an existing Augur instance (e.g., with replica data), or
Spin up a local instance and populate it with repository data of your choosing.
Set your PostgreSQL credentials in ui.py and the mcp_execute.py

4. **Register the MCP tool server**
```bash
  python register_mcp.py
```
5. **Run the Streamlit UI**
6. ```bash
     streamlit ui.py run
   ```
Once running, the chatbot can answer a wide range of schema-aware questions about the Augur database. [ADD SAMPLE QUERIES]

Under the hood, the tool uses a hybrid tool-calling approach with a customized schema retriever and Model Context Protocol (MCP) execution layer, ensuring SQL queries are grounded in the actual structure of your Augur instance.
   
