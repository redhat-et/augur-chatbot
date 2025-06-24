import json
import requests
import pickle
from sklearn.neighbors import NearestNeighbors

OLLAMA_URL = "http://localhost:11434/api/embeddings"
MODEL_NAME = "nomic-embed-text"
SCHEMA_PATH = "augur_schema.json"
EMBED_PATH = "augur_schema_embeddings.pkl"

TABLE_DESCRIPTIONS = {
    "repo": "Contains metadata about each repository including name, URLs, and timestamps.",
    "contributors": "Stores unique contributor identities across repositories, including login and email.",
    "commits": "Records commit-level information like author, timestamps, and commit hashes.",
    "pull_requests": "Holds data about pull requests including creation and merge info.",
    "issues": "Tracks issues submitted to repositories including title, status, and timestamps.",
    "contributor_affiliations": "Links contributors to their company affiliations and time ranges.",
    "repo_labor": "Provides labor hours estimated per repository over time.",
    "repo_dependencies": "Tracks declared dependencies used by each repository.",
    "repo_deps_scorecard": "Provides scores from security and reliability audits of dependencies.",
    "repo_deps_libyear": "Captures how outdated a dependency is in terms of version release date.",
    "releases": "Contains tagged releases and related metadata.",
    "pull_request_reviews": "Tracks review activity on pull requests by contributors.",
    "pull_request_commits": "Links commits to pull requests they were part of.",
    "pull_request_files": "Lists files modified in pull requests.",
    "issue_events": "Logs timeline events related to issues (e.g. closed, reopened).",
    "pull_request_events": "Logs timeline events related to pull requests.",
    "message": "Stores commit messages and other text payloads from contributions.",
    "commit_messages": "Join table between commits and messages for RAG tracking."
}

# Load schema and format table + column info, with optional descriptions
def load_schema():
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)

    descriptions = []
    table_names = []

    for table, columns in schema.items():
        base = f"Table `{table}` with columns: {', '.join(columns)}"
        if table in TABLE_DESCRIPTIONS:
            desc = f"{base}. Use case: {TABLE_DESCRIPTIONS[table]}"
        else:
            desc = base
        descriptions.append(desc)
        table_names.append(table)

    return table_names, descriptions

# Embedding wrapper using Ollama
def get_embeddings(texts):
    embeddings = []
    for text in texts:
        response = requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "prompt": text},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        embeddings.append(response.json()["embedding"])
    return embeddings

# Embed and save schema context
def embed_and_save():
    table_names, descriptions = load_schema()
    print(f"Embedding {len(descriptions)} table descriptions...")
    embeddings = get_embeddings(descriptions)

    with open(EMBED_PATH, "wb") as f:
        pickle.dump((embeddings, table_names, descriptions), f)

    print(f" Saved embeddings to {EMBED_PATH}")

# Given a user query, return relevant table descriptions
def get_schema_context(query, top_k=5):
    with open(EMBED_PATH, "rb") as f:
        embeddings, table_names, descriptions = pickle.load(f)

    query_embedding = get_embeddings([query])[0]
    knn = NearestNeighbors(n_neighbors=top_k, metric="cosine")
    knn.fit(embeddings)

    distances, indices = knn.kneighbors([query_embedding])
    return [descriptions[i] for i in indices[0]]

# CLI
if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2 and sys.argv[1] == "embed":
        embed_and_save()

    elif len(sys.argv) > 2 and sys.argv[1] == "ask":
        question = " ".join(sys.argv[2:])
        print("\n Relevant schema context:")
        for item in get_schema_context(question):
            print("-", item)

    else:
        print("Usage:")
        print("  python schema_rag.py embed")
        print("  python schema_rag.py ask <query>  ")
