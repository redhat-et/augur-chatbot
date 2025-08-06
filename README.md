# Augur Chatbot


This project is a database chat assistant for querying the [CHAOSS Augur](https://chaoss.github.io/augur/) open source software community metrics platform. Augur can collect and organizes GitHub data for thousands of repositories to help stakeholders understand contributor behavior, project health, and community trends.
This chatbot enhances connects with Augur by enabling users to ask questions in natural language and receive accurate, SQL-grounded answers powered by an LLM. It's designed for people who want quick insights into open source projects or company-level impact without needing to write SQL. Under the hood, the tool uses a hybrid tool-calling approach with a customized schema retriever and Model Context Protocol (MCP) execution layer, ensuring SQL queries are grounded in the actual structure of your Augur instance.

---
## Requirements
- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) python dependency manager
- [Ollama](https://ollama.com/) (for running LLaMA models locally)
- [Podman](https://podman.io/) (or Docker)
- Podman compose (or Docker compose)
- A running [Augur](https://github.com/chaoss/augur) PostgreSQL database and credentials to access it

## Setup
To get started:
1. **Clone the repo**
```bash
git clone https://github.com/redhat-et/augur-chatbot.git
cd augur-chatbot
```
2. **Create a .env file with your Augur Database credentials**
You can either:
Connect to an existing Augur instance (e.g., with replica data), or
Spin up a local instance and populate it with repository data of your choosing.

Create a .env file in the root directory by copying the example file. Then fill in your database credentials:
```bash
cp .env.example .env
```

5. **Pull the models**
To ensure the models are downloaded and ready to go, run `make pull_models` or run the following commands:
```
ollama pull nomic-embed-text
ollama pull llama3.2:3b-instruct-fp16
```
This will require ~ 7GB of free space on your machine.

6. **Start the chatbot stack**
Run `podman compose up --build` to pull or build the relevant containers and bring the chatbot stack up.

7. **Register the MCP tool server**
If this is the first time running the chatbot, run `make register_mcp` with the chatbot stack running - this will tell llamastack about the custom MCP server this chatbot uses to execute SQL.


Once running, the chatbot can answer a wide range of schema-aware questions about the Augur database.
Instructions for use:
- Repos, projects, and repo groups are indexed through a unique `repo_id` or `repo_group_id`. You should ask Augur Assistant the id for your intended project and use that in subsequent queries
- Follow the wordings of the tested queries below for optimal use and results
  
## Supported Queries
**Repo Lookup**
- What is the repo id for `<REPO_NAME>`?
- Show me the last update timestamp for repository `<REPO_ID>`.
- What is the repo group id for `<REPO_NAME>`?
- Which repos are part of rg `<REPO_GROUP_ID>`?

**Contributors & Affiliation**
- Who are the distinct cmt authors to repo id `<REPO_ID>`?
- Who is the top author to repo `<REPO_ID>`?
- Which contributors from Red Hat have worked on `<PROJECT_OR_ID>`?
- get_contributor_affiliations, project `<PROJECT_OR_ID>`, company Red Hat

**Repo health**
- How many open issues are in repo `<REPO_ID>`?
- How many issues were opened in repo `<REPO_ID>` in June 2025?
- Which repos haven’t been updated in over 90 days?

**Code & Languages**
- What are the programming languages used in repo `<REPO_ID>`?
- List the repo names that use Java.



   
