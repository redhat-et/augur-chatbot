## Code to embed database schema and store in a pkl

import json
import pickle
import requests
import re
from sklearn.neighbors import NearestNeighbors
from typing import List, Tuple
from dotenv import load_dotenv
import os
load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/embeddings")
MODEL_NAME = "nomic-embed-text"
SCHEMA_PATH = "data/augur_schema.json"
COLUMN_EMBED_PATH = "data/augur_column_embeddings.pkl"

JOIN_PATHS = {
    ("commits",      "repo_id"): ["repo"],
    ("repo_info",    "repo_id"): ["repo"],
    ("repo_labor",   "repo_id"): ["repo"],
    ("repo_groups",  "repo_id"): ["repo"]
}

# Get column meaning based on suffix
def infer_column_meaning(column_name: str, table_name: str) -> str:
    col = column_name.lower()
    patterns = {
        r'.*_id$': 'unique identifier',
        r'repo_id': 'repository identifier (join with repo)',
        r'cmt_ght_author_id': 'commit author (join with contributors)',
        r'repo_name': 'repository name'
    }
    for pattern, description in patterns.items():
        if re.match(pattern, col):
            return description
    return f"{table_name} {column_name.replace('_', ' ')}"

# Loading from augur_schema.json
def load_schema_for_columns():
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)
    column_descriptions = []
    column_keys = []
    for table_name, metadata in schema["tables"].items():
        table_desc = metadata.get("description", "")
        columns = metadata.get("columns", {})
        for column_name, col_meta in columns.items():
            key = f"{table_name}.{column_name}"
            meaning = col_meta.get("description", infer_column_meaning(column_name, table_name))
            joins = JOIN_PATHS.get((table_name, column_name), [])
            join_str = f" Possible joins: {', '.join(joins)}" if joins else ""
            full_desc = f"{key} — {meaning}. Table context: {table_desc}.{join_str}"
            column_descriptions.append(full_desc)
            column_keys.append((table_name, column_name))
    return column_keys, column_descriptions

# Store embeddings in a list
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

# Filtering and "choosing tables and columns" logic using KNN and cosine similarity
def get_schema_context(query: str) -> str:
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)

    table_descriptions = [f"Table {t}: {meta.get('description', '')}" for t, meta in schema["tables"].items()]
    table_keys = list(schema["tables"].keys())
    table_embeddings = get_embeddings(table_descriptions)
    query_embedding = get_embeddings([query])[0]

    table_knn = NearestNeighbors(n_neighbors=min(5, len(table_embeddings)), metric="cosine")
    table_knn.fit(table_embeddings)
    _, table_indices = table_knn.kneighbors([query_embedding])
    selected_tables = set([table_keys[i] for i in table_indices[0]])

    with open(COLUMN_EMBED_PATH, "rb") as f:
        column_embeddings, column_keys, column_descriptions = pickle.load(f)

## Use column descriptions and embeddings to match schema to query
    filtered = [
        (i, key, column_descriptions[i], column_embeddings[i])
        for i, key in enumerate(column_keys)
        if key[0] in selected_tables
    ]

    if not filtered:
        return "No matching schema found."

## identifies relevant list of columns for selected tables

    table_column_map = {table: [] for table in selected_tables}
    for t in list(table_column_map.keys()):
        cols = table_column_map[t]
        # Keep only the top 3 semantically relevant columns
        table_column_map[t] = cols[:3]
    filtered_keys = [key for _, key, _, _ in filtered]
    filtered_embs = [vec for _, _, _, vec in filtered]
# Using cosine similarity, find the top 15 relevant cols to user query
    col_knn = NearestNeighbors(n_neighbors=min(10, len(filtered_embs)), metric="cosine")
    col_knn.fit(filtered_embs)
    _, col_indices = col_knn.kneighbors([query_embedding])

    # add context to map
    additional_tables = set()
    for idx in col_indices[0]:
        t, c = filtered_keys[idx]
        table_column_map[t].append(c)
        join_paths = JOIN_PATHS.get((t, c), [])
        additional_tables.update(join_paths)

    for table in additional_tables:
        if table not in table_column_map and table in schema["tables"]:
            columns = list(schema["tables"][table]["columns"].keys())
            table_column_map[table] = columns[:6]

    schema_lines = []
    ## adding augur_data prefix so sql will execute
    for table, columns in table_column_map.items():
        if columns:
            column_list = ", ".join([f"{table}.{col}" for col in columns])
            schema_lines.append(f"augur_data.{table}({column_list})")

    return "\n".join(schema_lines)

# Embed and save to .pkl
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
        print("\n Simulating retrieval for:", query)
        print("\n" + get_schema_context(query))
    else:
        print("Usage:")
        print("  python schema_rag.py embed        # Embed and save column schema")
        print("  python schema_rag.py ask <query>  # Retrieve schema context")
