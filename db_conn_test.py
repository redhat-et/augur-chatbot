from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.lib.agents.event_logger import EventLogger
from llama_stack_client import LlamaStackClient
import argparse
import logging
import os
from dotenv import load_dotenv
import psycopg2

from mcp_tools.rna import query_rna_by_type
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# CLI arguments
parser = argparse.ArgumentParser()
parser.add_argument("-r", "--remote", help="Use remote LlamaStack server", action="store_true")
parser.add_argument("-s", "--session-info-on-exit", help="Print agent session info on exit", action="store_true")
parser.add_argument("-a", "--auto", help="Run preset examples automatically", action="store_true")
args = parser.parse_args()

model = "meta-llama/Llama-3.2-3B-Instruct"

# Base URL setup
if args.remote:
    base_url = os.getenv("REMOTE_BASE_URL")
else:
    base_url = "http://localhost:8321"

client = LlamaStackClient(base_url=base_url)
logger.info(f"Connected to Llama Stack server @ {base_url}")

# Connect to RNAcentral public postgres
conn_string = "host='hh-pgsql-public.ebi.ac.uk' dbname='pfmegrnargs' user='reader' password='NWDMCE5xdipIjRrp'"
conn = psycopg2.connect(conn_string)
cur = conn.cursor()

#  want to dynamically inject schema info
schema_description = ""
cur.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema='public' AND table_type='BASE TABLE';
""")
tables = cur.fetchall()

for (table_name,) in tables:
    schema_description += f"\nTABLE: {table_name}\n"
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = %s;
    """, (table_name,))
    columns = cur.fetchall()
    for column_name, data_type in columns:
        schema_description += f"- {column_name} ({data_type})\n"

# Define the agent with dynamic schema injected

agent = Agent(
    client,
    model=model,
    instructions="You can use tools to query RNA data.",
    tools=["mcp::custom_tool", query_rna_by_type],
    tool_config={"tool_choice": "auto"},
)


# Auto mode
if args.auto:
    user_prompts = [
        "List 5 distinct RNA types in the database.",
        "Which organisms (common name) have RNA with taxid 9606?",
        "How many unique UPIs are there in the RNA table?"
    ]

    session_id = agent.create_session(session_name="Auto_demo")

    for prompt in user_prompts:
        print(f"\n USER: {prompt}")
        turn_response = agent.create_turn(
            messages=[{"role": "user", "content": prompt}],
            session_id=session_id,
            stream=True,
        )

        sql_code = None
        for log in EventLogger().log(turn_response):
            log.print()
            if "```sql" in log.content:
                sql_code_raw = log.content.split("```sql")[1].split("```")[0]
                sql_code = " ".join(sql_code_raw.split())

        if sql_code:
            print(f"\nRunning SQL:\n{sql_code}")
            try:
                cur.execute(sql_code)
                rows = cur.fetchall()
                for row in rows:
                    print(row)
            except Exception as e:
                print("Error:", e)

    cur.close()
    conn.close()

# Manual mode
else:
    session_id = agent.create_session(session_name="Conversation_demo")

    while True:
        user_input = input(">>> ")
        if "/bye" in user_input:
            if args.session_info_on_exit:
                session_info = client.agents.session.retrieve(session_id=session_id, agent_id=agent.agent_id)
                print(session_info.to_dict())
            break

        turn_response = agent.create_turn(
            session_id=session_id,
            messages=[{"role": "user", "content": user_input}],
            stream=True,
        )

        sql_code = None
        for log in EventLogger().log(turn_response):
            log.print()
            if "```sql" in log.content:
                sql_code_raw = log.content.split("```sql")[1].split("```")[0]
                sql_code = " ".join(sql_code_raw.split())

        if sql_code:
            print(f"\nRunning SQL:\n{sql_code}")
            try:
                cur.execute(sql_code)
                rows = cur.fetchall()
                for row in rows:
                    print(row)
            except Exception as e:
                print("Error:", e)

    cur.close()
    conn.close()
