from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.lib.agents.event_logger import EventLogger
from llama_stack_client import LlamaStackClient
import argparse
import logging
import os
from dotenv import load_dotenv
import psycopg2
import json
from schema_rag import get_schema_context, get_relevant_tables  # updated RAG imports
import time

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

logging.getLogger("llama_stack_client").setLevel(logging.WARNING)

'''

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

    schema_text = "\n".join(
        f"Table: {table}\n- " + "\n- ".join(columns) + "\n"
        for table, columns in schema_dict.items()
    )

    cur.close()
    conn.close()

    return schema_text
'''

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

parser = argparse.ArgumentParser()
parser.add_argument("-r", "--remote", help="Use remote LlamaStack server", action="store_true")
parser.add_argument("-s", "--session-info-on-exit", help="Print agent session info on exit", action="store_true")
parser.add_argument("-a", "--auto", help="Run preset examples automatically", action="store_true")
args = parser.parse_args()

model = "llama3.2:3b-instruct-fp16"

base_url = os.getenv("REMOTE_BASE_URL") if args.remote else "http://localhost:8321"
client = LlamaStackClient(base_url=base_url)
logger.info(f" Connected to Llama Stack server @ {base_url}")

instructions = """
Step 1: User asks a quesion. Understand the question
Step 2: Retrieve relevant schema context tables and columns
Step 3: Classify intent. Is it a frequently asked question? Yes - call the correct mcp::sql tool: 
- get_top_contributors 
- get_pr_reviewers 
- get_top_languages_by_repo_name
- get_monthly_contributions
- get_contributor_contact_info
- get_contributor_affiliations
Step 4: If the question does not match a known tool, always generate and run the correct SQL using execute_sql. 
You must only use tables and columns that appear in the schema context.
"""

agent = Agent(
    client=client,
    model=model,
    instructions=instructions,
    tools=["mcp::sql"],
    tool_config={"tool_choice": "auto"},
    sampling_params={"max_tokens": 4096, "strategy": {"type": "greedy"}},
)

session_id = agent.create_session("ManualSession")

while True:
    user_input = input(">>> ").strip()
    time.sleep(2)

    if user_input.lower() in ["/bye", "exit"]:
        if args.session_info_on_exit:
            info = client.agents.session.retrieve(session_id=session_id, agent_id=agent.agent_id)
            print(info.to_dict())
        break

    # 🔍 Step 2: Get full schema context
    context_str = get_schema_context(user_input)

    # Inject context into user prompt
    full_prompt = f"""
    You may use the following schema context to answer the user's question.
    {context_str}

    User question: {user_input}
    """
       # 🔍 Step 1: Retrieve relevant tables (for debugging)
    debug_tables = get_relevant_tables(user_input)
    logger.info(f">>> [DEBUG] Relevant tables selected by embeddings: \n" + full_prompt)

    turn = agent.create_turn(
        session_id=session_id,
        messages=[{"role": "user", "content": full_prompt}],
        stream=True,
    )

    for log in EventLogger().log(turn):
        log.print()
