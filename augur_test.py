# Code bellow written following examples here: https://llama-stack.readthedocs.io/en/latest/building_applications
from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.lib.agents.event_logger import EventLogger
from llama_stack_client import LlamaStackClient
from termcolor import cprint
import argparse
import logging
import os
from dotenv import load_dotenv

#from client_tools import torchtune

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


parser = argparse.ArgumentParser()
parser.add_argument("-r", "--remote", help="Uses the remote_url", action="store_true")
parser.add_argument("-s", "--session-info-on-exit", help="Prints agent session info on exit", action="store_true")
parser.add_argument("-a", "--auto", help="Automatically runs examples, and does not start a chat session", action="store_true")
args = parser.parse_args()

model="meta-llama/Llama-3.2-3B-Instruct"

# Connect to a llama stack server
if args.remote:
    base_url = os.getenv("REMOTE_BASE_URL")
    mcp_url = os.getenv("REMOTE_MCP_URL")
else:

    ## point this to llamastack on cluster that has larger models
    base_url="http://localhost:8321"
    mcp_url="http://127.0.0.1:8000/sse"


client = LlamaStackClient(base_url=base_url)
logger.info(f"Connected to Llama Stack server @ {base_url} \n")


""" #### TESTING ######
# Register MCP tool group if not already registered
registered_toolgroups = [tg.id for tg in client.toolgroups.list()]
if "mcp" not in registered_toolgroups:
    client.toolgroups.register(
        toolgroup_id="mcp",
        provider_id="model-context-protocol",
        mcp_endpoint={"uri": mcp_url},
    )

# Confirm tools are registered (optional debug)
mcp_tools = [t.identifier for t in client.tools.list(toolgroup_id="mcp")]
print(f"✅ Registered MCP tools: {mcp_tools}")
#### END TESTING ###### """

agent = Agent(
    client,
    model=model,
    instructions="""You are a helpful AI assistant that answers questions about the database provided.

You are working with a PostgreSQL database that contains information about RNA sequences and species. The tables include:

TABLE: rna
- upi (text)
- taxid (int)
- rna_type (text)
- seq_short (text)

TABLE: xref
- upi (text)
- database (text)
- accession (text)
- version (text)

TABLE: species
- taxid (int)
- scientific_name (text)
- common_name (text)

Only use the tables and columns listed above. If the information is not available in the schema, say you don't know.
""",
    
)



if args.auto:
    user_prompts = ["""hello"""]
    session_id = agent.create_session(session_name="Auto_demo")
    for prompt in user_prompts:
        turn_response = agent.create_turn(
            messages=[
                {
                    "role":"user",
                    "content": prompt
                }
            ],
            session_id=session_id,
            stream=True,
        )
        for log in EventLogger().log(turn_response):
            log.print()

else:
    #Create a chat session
    session_id = agent.create_session(session_name="Conversation_demo")
    while True:
        user_input = input(">>> ")
        if "/bye" in user_input:
            if args.session_info_on_exit:
                agent_session = client.agents.session.retrieve(session_id=session_id, agent_id=agent.agent_id)
                print( agent_session.to_dict())
            break
        turn_response = agent.create_turn(
            session_id=session_id,
            messages=[{"role": "user", "content": user_input}],
        )

        for log in EventLogger().log(turn_response):
            log.print()
