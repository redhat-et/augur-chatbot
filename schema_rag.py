import json
import pickle
import requests
from sklearn.neighbors import NearestNeighbors

OLLAMA_URL = "http://localhost:11434/api/embeddings"
MODEL_NAME = "nomic-embed-text"
SCHEMA_PATH = "augur_schema.json"
EMBED_PATH = "augur_schema_embeddings.pkl"

#  Load schema and build descriptions

def load_schema_descriptions():
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)

    descriptions = []
    table_keys = []

    for table, metadata in schema.items():
        column_list = metadata.get("columns", [])
        column_text = ", ".join(column_list)
        desc = metadata.get("description", "")
        full_text = f"Table `{table}` with columns: {column_text}. {desc}"
        descriptions.append(full_text)
        table_keys.append(table)

    return table_keys, descriptions

# Get embeddings using Ollama

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

# Embed and save

def embed_and_save():
    table_keys, descriptions = load_schema_descriptions()
    print(f"Embedding {len(descriptions)} table descriptions...")
    embeddings = get_embeddings(descriptions)

    with open(EMBED_PATH, "wb") as f:
        pickle.dump((embeddings, table_keys, descriptions), f)

    print(f" Saved embeddings to {EMBED_PATH}")

# Retrieve top-k relevant schema for a query

def get_schema_context(query, top_k=5):
    with open(EMBED_PATH, "rb") as f:
        embeddings, table_keys, descriptions = pickle.load(f)

    query_embedding = get_embeddings([query])[0]

    knn = NearestNeighbors(n_neighbors=top_k, metric="cosine")
    knn.fit(embeddings)

    distances, indices = knn.kneighbors([query_embedding])
    return [
        {
            "table": table_keys[i],
            "description": descriptions[i]
        } for i in indices[0]
    ]

# CLI
if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2 and sys.argv[1] == "embed":
        embed_and_save()

    elif len(sys.argv) > 2 and sys.argv[1] == "ask":
        question = " ".join(sys.argv[2:])
        print("\n Relevant schema context:")
        for item in get_schema_context(question):
            print("-", item["description"])

    else:
        print("Usage:")
        print("  python schema_rag.py embed        # Build and save schema embeddings")
        print("  python schema_rag.py ask <query>  # Get relevant schema for a question")
