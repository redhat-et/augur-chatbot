Sahana Sreeram - Software Engineering Intern

Working Repo:
[[https://github.com/redhat-et/augur-chatbot]{.underline}](https://github.com/redhat-et/augur-chatbot)

### Background & Motivation

Augur Assistant transforms how Red Hat and the CHAOSS community access
project health data by layering a natural-language agent over our
OSPO-managed Augur database of 40K+ repositories. The capabilities and
goals of the tool are as follows:

-   Accessible Insights: Enables non-technical users (community
    managers, contributors) to run complex queries without SQL

-   Boosts visibility: Scans real-time metrics on Red Hat's open-source
    footprint and contributor affiliations, activity trends, license
    breakdowns

-   Proves small-model inference: Validated a lightweight MCP-powered
    pipeline (Llama Instruct 3B) for domain-specific agents, opening the
    door to low-latency, tool-exec AI workflows across the organization.

### Tech Stack
|  Layer                 |  Component                          |  Role & Description                                                                                                                                                              |
|------------------------|-------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|  Model Serving         |  Ollama                             |  <br>Self-hosted Llama models (3B or 7B Instruct) served via Ollama                                                                                                              |
|  Agent Orchestration   |  LlamaStack Agent                   |  <br> Interprets “use execute_sql()” instructions<br> <br>Emits structured execute_sql(sql="…") calls                                                                            |
|  Schema Retrieval      |  FAISS DB (stored in data folder)   |  <br> Takes in prewritten schema via augur_schema.json<br> <br> Uses embedding model and saves to data<br> <br>Indexes them for fast top-k lookup of relevant schema snippets    |
|  Tooling protocol      |  MCP Server                         |  <br> Registers custom-written mcp_execute server<br> <br>Routes LLM-generated SQL to the database connector                                                                     |
|  Data Source           |  Postgres Augur DB                  |  <br> Read-only use of Augur DB<br> <br>Connects via .env variables and database credentials                                                                                     |
|  Frontend              |  Streamlit UI                       |  <br> Optional SQL toggle and debug trace<br> <br>Regex-driven parsing to render JSON results as clean text                                                                      |

![CHATBOT SCHEMA - Page 1.jpeg](./Architecture Diagram.png){width="10.191686351706037in" height="5.78417104111986in"}


### Future planning:

|  Challenge                                                                      |  Next Actions                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|  Polish Final Output<br> <br> Human-readable results only, get rid of SQL dump  |  Enhance ui.py with regex/JSON hooks to surface only human-readable text (with an optional toggle for raw output).                                                                                                                                                                                                                                                                                                                                                                                                                |
|  Simplify setup                                                                 |  Create a docker-compose that simplifies all the setup commands                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
|  Fix Intent Parsing step by reducing model hallucination                        |  Challenge: Small-model errors and edge-case phrasing.<br> <br>Next:<br> <br> <br> Embed few-shot Q→SQL examples in the prompt.<br> <br> Test larger models or non-Llama models. 7B versions seem to work much better than 3B<br> <br>Better prompt tuning                                                                                                                                                                                                                                                                        |
|  Modular Agent-to-Agent Pipeline                                                |  Challenge: A monolithic agent struggles to juggle schema retrieval, SQL generation, execution and output formatting all at once.<br> <br> <br>  			<br> <br> Next:<br> <br> Split responsibilities into specialized agents:<br> <br> <br> Schema Agent – selects top K tables/columns<br> <br> SQL Agent – builds valid queries<br> <br> Execution Agent – runs the SQL via MCP<br> <br> Output Agent – parses and converts to NL <br> <br> <br>  			<br> <br> Orchestrate them in a lightweight workflow (feedback per Josh Berkus).  |
|  Build an Augur Playground for Red Hatters to access without setup              |  Challenge: Requires individual Augur instances/credentials.<br> <br>Next:<br> <br> <br> Offer a managed “playground” Augur DB pre-loaded with RH data.<br> <br> Provide a one-click Docker/SQLite snapshot for local demos.<br> <br> Implement role-based access for unredacted metrics.                                                                                                                                                                                                                                         |
|  Broaden integration                                                            |  A last step could be to turn Augur Assistant into a Red Hat-specific Discord bot, or integrate with Ask Red Hat                                                                                                                                                                                                                                                                                                                                                                                                                  |

### Project ownership

-   Handoff to OSPO (post-Summer 2025)

    -   Formal transfer of code, documentation, and support for future
        planning responsibilities

-   Upstream community

    -   Opportunity to partner with the upstream CHAOSS community in the
        Data Science Working Group

    -   Some members of the community have expressed interest in
        AI/ML/agentic workflows. This project could be an area for them
        to work on. \*\* Especially integration with A2A

-   Long-term support:

    -   OSPO to maintain the production-hosted Augur Assistant instance.

    -   CHAOSS to own the open-source roadmap, issue triage, and model
        updates.
