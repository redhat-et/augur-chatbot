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
from prompt_template import AUGUR_AGENT_PROMPT
import logging

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

# Enable debugging for the Stack client and its HTTPX/SSE transport
logging.getLogger("llama_stack_client").setLevel(logging.WARNING)
#logging.getLogger("httpx").setLevel(logging.DEBUG)
#logging.getLogger("websockets").setLevel(logging.DEBUG)


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
    important_tables = {
        "repo",
        "contributors",
        "commits",
        "pull_requests",
        "pull_request_reviews",
        "contributor_affiliations",
        "repo_groups",
        "contributor_repo"
    }

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
        if table in important_tables:
            schema_dict.setdefault(table, []).append(f"{column} ({dtype})")

    # Format as string
    schema_text = "\n".join(
        f"Table: {table}\n- " + "\n- ".join(columns) + "\n"
        for table, columns in schema_dict.items()
    )

    cur.close()
    conn.close()

    return schema_text


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

model = "llama3.2:3b-instruct-fp16"

if args.remote:
    base_url = os.getenv("REMOTE_BASE_URL")
else:
    base_url = "http://localhost:8321"

client = LlamaStackClient(base_url=base_url)
logger.info(f"✅ Connected to Llama Stack server @ {base_url}")

schema = def_schema()
#print(schema)

table_descriptions = json.dumps(TABLE_DESCRIPTIONS, indent=2)


# Agent instructions


instructions = """

Step 1: understand database schema. 
Step 2: User asks question. Understand question
Step 3: Classify intent. Is it a frequently asked question? Yes - call the correct mcp::sql tool: 
- get_top_contributors 
- get_pr_reviewers 
- get_top_languages_by_repo_name
- get_monthly_contributions
- get_contributor_contact_info
- get_contributor_affiliations
Step 4: Not a frequently asked question? Generate and RUN the correct sql using execute_sql. Keep executing sql until you get the correct query.
Step 5: Output answer to user.

Walk user through reasoning. Answer question correctly.
Important tables:
    "augur_data.repo",
    "augur_data.contributors",
    "augur_data.commits",
    "augur_data.pull_requests",
    "augur_data.pull_request_reviews",
    "augur_data.contributor_affiliations",
    "augur_data.repo_groups",
    "augur_data.contributor_repo"

"""


'''"repo",
    "contributors",
    "commits",
    "pull_requests",
    "pull_request_reviews",
    "contributor_affiliations",
    "repo_groups",
    "contributor_repo"
instructions = AUGUR_AGENT_PROMPT.format(
    tools="""
The following tools are available:
- get_contributor_contact_info_by_affiliation
- get_top_contributors
- get_pr_reviewers
- get_top_languages_by_repo_group
- get_monthly_contributions
- list_objects
- execute_sql

You must understand the database schema to execute correct sql.
{schema}
"""
)
'''

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
        "Count the number of repos using sql",
        "Using FAQ, Get the top 10 contributors for all repos",
        "Who are the top 10 contributors in project augur?",
        "What is the monthly contribution activity for project augur in January 2024",
        "Show me all the contributors in project augur affiliated with Red Hat",
        "Using get_top_languages, what are the programming languages in project augur?",
        "Who are the PR reviewers in project augur?"
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
    turn = agent.create_turn(
    session_id=session_id,
    messages=[
        {
            "role": "system",
            "content": f"""
    Use the tables in {schema} to query.
    """
            },
            {"role": "user", "content": user_input}
        ],
        stream=True,
    )
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


