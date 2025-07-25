import streamlit as st
import pandas as pd
import numpy as np
from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.lib.agents.event_logger import EventLogger
from llama_stack_client import LlamaStackClient
import logging
import os
from dotenv import load_dotenv
import json
from schema_rag import get_schema_context
import re

# Streamlit Page Config
st.set_page_config(page_title="Augur SQL Assistant", layout="wide")
st.markdown("<h1 style='color:#2c3e50'> Augur SQL Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size:16px;'>Ask a question about the Augur PostgreSQL database.</p>", unsafe_allow_html=True)

# Logger
logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Load .env and Connect
load_dotenv()
base_url = os.getenv("BASE_URL")
client = LlamaStackClient(base_url=base_url)
request_timeout=int(os.getenv("LLM_TIMEOUT", "120"))

# LLM Instructions
instructions = """
You are a SQL query expert for the CHAOSS Augur PostgreSQL database.
You must always call the `execute_query()` tool
Whenever the user asks about contributor affiliations—keywords like “company,” “affiliation,” “Red Hat,” “domain,” etc.—you must call the get_contributor_affiliations function instead of generating SQL yourself.
TASK:
- Convert the user's natural language input into a valid SQL query using only the provided schema context.
- Use only the `execute_query(sql="...")` tool to run the query.
- If a project is mentioned by name (e.g. "augur"), first retrieve its `repo_id` using:
   SELECT repo_id FROM augur_data.repo WHERE repo_name = 'repo_name'
- Join tables on `repo_id`

CONTEXT:
- For each user input, you will receive a relevant subset of the database (tables + columns)
- Your SQL MUST reference ONLY these tables/columns.
- You have NO access to other tools or schema metadata beyond what's provided.

DO NOT:
- Do not use tables or columns not in schema context
- Do not fabricate or assume data
- Do not use any other tools besides `execute_query`
"""

agent = Agent(
    client=client,
    model="llama3.2:3b-instruct-fp16",
    instructions=instructions,
    tools=["mcp::execute"],
    tool_config={"tool_choice": "auto"},
    sampling_params={"max_tokens": 4096, "strategy": {"type": "greedy", "temperature": 0.0}},
)
session_id = agent.create_session("StreamlitSession")

# main.py logic, reformatted with streamlit
user_input = st.text_input(" Ask a question:", placeholder="e.g., Count contributors per repo with over 1000 contributors")
show_sql = st.checkbox("🔍 Show SQL Query")

if st.button("Submit") and user_input:
    with st.spinner("Thinking..."):
        context_str = get_schema_context(user_input)

        full_prompt = f"""
You may use the following schema context to answer the user's question.
{context_str}

User question: {user_input}
"""

        # Show context block
        st.markdown("### Schema Context")
        st.markdown(
            f"<div style='background-color:#f8f9fa; padding:10px; border-radius:8px'><pre>{context_str}</pre></div>",
            unsafe_allow_html=True
        )

        # Show prompt
        st.markdown("### Prompt Sent to LLM")
        st.markdown(
            f"<div style='background-color:#f0f0f0; padding:10px; border-radius:8px'><pre>{full_prompt.strip()}</pre></div>",
            unsafe_allow_html=True
        )

        # Get response
        st.markdown("### LLM Response")
        output_container = st.empty()
        full_response = ""
        final_response_triggered = False

        turn = agent.create_turn(
            session_id=session_id,
            messages=[{"role": "user", "content": full_prompt}],
            stream=True
        )

        for log in EventLogger().log(turn):
            if log.content:
                full_response += log.content
                output_container.markdown(
                    f"<div style='background-color:#e8f5e9; padding:10px; border-radius:8px;'><pre>{full_response}</pre></div>",
                    unsafe_allow_html=True
                )

                # Stop if final response detected
                if re.match(r"^(Response|The\s)", log.content.strip()):
                    final_response_triggered = True
                    break

        # Parse and display extracted SQL
        if show_sql:
            st.markdown("### SQL Query")
            sql_match = re.search(r'execute_query\(sql\s*=\s*"([^"]+)"\)', full_response, re.DOTALL)
            if sql_match:
                cleaned_sql = sql_match.group(1).strip()
                st.code(cleaned_sql, language="sql")
            else:
                st.warning("No SQL query found.")

        # Final answer parsing
        st.markdown("### Final Answer")
        final_match = re.search(r'Response:\\s*(\\{.*\\})', full_response, re.DOTALL)
        if final_match:
            raw_json = final_match.group(1)
            try:
                parsed = json.loads(raw_json)
                pretty = json.dumps(parsed, indent=2)
                st.markdown(f"<pre>{pretty}</pre>", unsafe_allow_html=True)
            except json.JSONDecodeError:
                st.write(raw_json)
        else:
            st.info("Could not extract a clear final answer. Please check the LLM response.")
