# schema_rag.py (enhanced with join-aware expansion)

import json
import pickle
import requests
import re
from sklearn.neighbors import NearestNeighbors
from typing import Dict, List, Tuple

OLLAMA_URL = "http://localhost:11434/api/embeddings"
MODEL_NAME = "nomic-embed-text"
SCHEMA_PATH = "augur_schema.json"
COLUMN_EMBED_PATH = "augur_column_embeddings.pkl"

# Known join paths for semantic expansion
JOIN_PATHS = {
    ("commits", "repo_id"): ["repo"],
    ("commits", "cmt_ght_author_id"): ["contributors"],
    ("pull_requests", "repo_id"): ["repo"],
    ("pull_requests", "pr_cntrb_id"): ["contributors"],
    ("pull_request_reviews", "pull_request_id"): ["pull_requests"],
    ("contributor_affiliations", "cntrb_id"): ["contributors"],
    ("repo", "repo_group_id"): ["repo_groups"]
}

def infer_column_meaning(column_name: str, table_name: str) -> str:
    col = column_name.lower()

    patterns = {
        r'.*_id$': 'unique identifier',
        r'repo_id': 'repository identifier (join with repo)',
        r'cntrb_id': 'contributor identifier (join with contributors)',
        r'cmt_ght_author_id': 'commit author (join with contributors)',
        r'pull_request_id': 'pull request identifier (join with pull_requests)',
        r'pr_cntrb_id': 'pull request contributor (join with contributors)',
        r'.*_at$': 'timestamp when event occurred',
        r'repo_name': 'repository name',
        r'cntrb_login': 'contributor username/login',
        r'cntrb_email': 'contributor email address',
        r'pr_src_state': 'pull request status (open/closed)',
    }

    for pattern, description in patterns.items():
        if re.match(pattern, col):
            return description

    return f"{table_name} {column_name.replace('_', ' ')}"

def load_schema_for_columns():
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)

    column_descriptions = []
    column_keys = []

    for table_name, metadata in schema.items():
        table_desc = metadata.get("description", "")
        columns = metadata.get("columns", [])

        for column_name in columns:
            key = f"{table_name}.{column_name}"
            meaning = infer_column_meaning(column_name, table_name)
            joins = JOIN_PATHS.get((table_name, column_name), [])
            join_str = f" Possible joins: {', '.join(joins)}" if joins else ""
            full_desc = f"{key} — {meaning}. Table context: {table_desc}.{join_str}"
            column_descriptions.append(full_desc)
            column_keys.append((table_name, column_name))

    return column_keys, column_descriptions

def get_embeddings(texts: List[str]) -> List[List[float]]:
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

def get_schema_context(query: str) -> str:
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)

    table_descriptions = [f"Table {t}: {meta.get('description', '')}" for t, meta in schema.items()]
    table_keys = list(schema.keys())
    table_embeddings = get_embeddings(table_descriptions)
    query_embedding = get_embeddings([query])[0]

    table_knn = NearestNeighbors(n_neighbors=min(5, len(table_embeddings)), metric="cosine")
    table_knn.fit(table_embeddings)
    _, table_indices = table_knn.kneighbors([query_embedding])
    selected_tables = set([table_keys[i] for i in table_indices[0]])

    with open(COLUMN_EMBED_PATH, "rb") as f:
        column_embeddings, column_keys, column_descriptions = pickle.load(f)

    filtered = [
        (i, key, column_descriptions[i], column_embeddings[i])
        for i, key in enumerate(column_keys)
        if key[0] in selected_tables
    ]

    if not filtered:
        return "No matching schema found."

    table_column_map = {table: [] for table in selected_tables}
    filtered_keys = [key for _, key, _, _ in filtered]
    filtered_embs = [vec for _, _, _, vec in filtered]

    col_knn = NearestNeighbors(n_neighbors=min(15, len(filtered_embs)), metric="cosine")
    col_knn.fit(filtered_embs)
    _, col_indices = col_knn.kneighbors([query_embedding])

    additional_tables = set()
    for idx in col_indices[0]:
        t, c = filtered_keys[idx]
        table_column_map[t].append(c)
        join_paths = JOIN_PATHS.get((t, c), [])
        additional_tables.update(join_paths)

    for table in additional_tables:
        if table not in table_column_map and table in schema:
            columns = schema[table]["columns"]
            table_column_map[table] = columns[:6]  # add a few default columns

    schema_lines = []
    for table, columns in table_column_map.items():
        if columns:
            column_list = ", ".join([f"{table}.{col}" for col in columns])
            schema_lines.append(f"augur_data.{table}({column_list})")

    return "\n".join(schema_lines)

def embed_and_save():
    print("Embedding columns with join-aware descriptions...")
    column_keys, column_descriptions = load_schema_for_columns()
    column_embeddings = get_embeddings(column_descriptions)

    with open(COLUMN_EMBED_PATH, "wb") as f:
        pickle.dump((column_embeddings, column_keys, column_descriptions), f)
    print(f"Saved column embeddings to {COLUMN_EMBED_PATH}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2 and sys.argv[1] == "embed":
        embed_and_save()
    elif len(sys.argv) > 2 and sys.argv[1] == "ask":
        query = " ".join(sys.argv[2:])
        print("\n🔍 Simulating retrieval for:", query)
        print("\n" + get_schema_context(query))
    else:
        print("Usage:")
        print("  python schema_rag.py embed        # Embed and save column schema")
        print("  python schema_rag.py ask <query>  # Retrieve schema context")
