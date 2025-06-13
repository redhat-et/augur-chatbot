# main.py

from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.lib.agents.event_logger import EventLogger
from llama_stack_client import LlamaStackClient
import argparse
import logging
import os
from dotenv import load_dotenv
import psycopg2
import json

import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

# Enable debugging for the Stack client and its HTTPX/SSE transport
logging.getLogger("llama_stack_client").setLevel(logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.DEBUG)
logging.getLogger("websockets").setLevel(logging.DEBUG)


# --- Constants ---
TABLE_DESCRIPTIONS = {
    "repo": "Stores GitHub repository metadata, including names, URLs, and creation dates. Each repository has a unique `repo_id`.",
    "contributors": "Tracks GitHub contributors, their unique IDs (`cntrb_id`), and GitHub login names (`gh_login`).",
    "commits": "Holds commit-level metadata. Links to contributors via `cmt_ght_author_id` and repositories via `repo_id`.",
    "pull_requests": "Logs pull request activity and metadata such as creation date, status, and repository.",
    "pull_request_reviews": "Contains review events linking to `pull_request_id` and `cntrb_id`.",
    "contributor_affiliations": "Maps contributors to organization affiliations via `ca_id` and `ca_affiliation`.",
    "repo_groups": "Groups multiple repositories into clusters using `rg_id`."
}


def def_schema():
    conn = psycopg2.connect(os.environ["DATABASE_URI"])
    cur = conn.cursor()

    cur.execute("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'augur_data'
        ORDER BY table_name, ordinal_position
    """)

    rows = cur.fetchall()

    schema_dict = {}
    for table, column, dtype in rows:
        schema_dict.setdefault(table, []).append(f"{column} ({dtype})")

    # Format as string
    schema_text = "\n".join(
        f"- {table}: " + ", ".join(columns)
        for table, columns in schema_dict.items()
    )

    cur.close()
    conn.close()

    return schema_text

def describe_schema_tool(input=None):
    return def_schema()

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# CLI arguments
parser = argparse.ArgumentParser()
parser.add_argument("-r", "--remote", help="Use remote LlamaStack server", action="store_true")
parser.add_argument("-s", "--session-info-on-exit", help="Print agent session info on exit", action="store_true")
parser.add_argument("-a", "--auto", help="Run preset examples automatically", action="store_true")
args = parser.parse_args()

# Model and base URL setup
model = "meta-llama/Llama-3.2-3B-Instruct"

if args.remote:
    base_url = os.getenv("REMOTE_BASE_URL")
else:
    base_url = "http://localhost:8321"

client = LlamaStackClient(base_url=base_url)
logger.info(f"✅ Connected to Llama Stack server @ {base_url}")

schema = def_schema()
table_descriptions = json.dumps(TABLE_DESCRIPTIONS, indent=2)

# Agent instructions

'''
instructions = f"""
You are a helpful and precise assistant with access to a PostgreSQL database via MCP tools:
- list_schemas
- list_objects
- execute_sql
- get_object_details
- explain_query

Full schema:
{schema}

Behavior guidelines:
1. Table and column names are lowercase.
2. Schema is always augur_data.
3. Always execute your SQL after generating it.
4. Retry with edits if the SQL fails.
5. Use joins across commits, contributors, and affiliations to map contributions.

Example prompt:
User: How many repos are in the database?
Execute the correct SQL command and output the answer.
"""
'''
instructions = f"""
You are an AI assistant with one tool available:
- mcp::postgres.execute_sql(sql: str) -> JSON rows

When you need to query the augur_data schema, emit exactly one JSON tool call, for example:
```json
{{ "tool": "mcp::postgres", "args": {{ "sql": "SELECT COUNT(*) FROM augur_data.repo;" }} }}
After the tool returns its JSON result, produce a clean natural-language answer.
For instance, if the result is [{{"count": 42}}], respond:

“There are 42 repositories in the database.”

Important:

Do not print raw SQL or any extra text when calling the tool.

Only emit the JSON object, wait for the tool_result, then answer.

All SQL must target tables in the augur_data schema.
"""

agent = Agent(
    client=client,
    model=model,
    instructions=instructions,
    tools=["mcp::postgres", "mcp::sql"],
    tool_config={"tool_choice": "auto"},
    sampling_params={"max_tokens": 4096, "strategy": {"type": "greedy"}},
)



# Auto mode
if args.auto:
    prompts = [
        "List all repos in the database.",
        "How many repos are in the database?",
        "How many contributors are in the database?"
    ]
    session_id = agent.create_session("AutoDemo")
    for i, prompt in enumerate(prompts):
        print(f"\nUSER: {prompt}")
        turn = agent.create_turn(
            messages=[{"role": "user", "content": prompt}],
            session_id=session_id,
            stream=True,
        )
        for log in EventLogger().log(turn):
            log.print()
    exit()

# Manual mode
session_id = agent.create_session("ManualSession")
while True:
    user_input = input(">>> ").strip()
    if user_input.lower() in ["/bye", "exit"]:
        if args.session_info_on_exit:
            info = client.agents.session.retrieve(session_id=session_id, agent_id=agent.agent_id)
            print(info.to_dict())
        break

    turn = agent.create_turn(
        session_id=session_id,
        messages=[{"role": "user", "content": user_input}],
        stream=True,
    )
    for log in EventLogger().log(turn):
        log.print()
