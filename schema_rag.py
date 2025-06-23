import json
import requests
import pickle
from sklearn.neighbors import NearestNeighbors

OLLAMA_URL = "http://localhost:11434/api/embeddings"
MODEL_NAME = "nomic-embed-text"
SCHEMA_PATH = "augur_schema.json"         # Your table+column JSON
EMBED_PATH = "augur_schema_embeddings.pkl"

# Step 1: Load schema and turn it into table descriptions
def load_schema():
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)

    descriptions = []
    table_names = []

    for table, columns in schema.items():
        desc = f"Table `{table}` with columns: {', '.join(columns)}"
        descriptions.append(desc)
        table_names.append(table)

    return table_names, descriptions

# Step 2: Embed using nomic-embed-text via Ollama
def get_embeddings(texts):
    embeddings = []
    for text in texts:
        response = requests.post(
            "http://localhost:11434/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": text},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        embeddings.append(response.json()["embedding"])
    return embeddings


# Step 3: Save embeddings
def embed_and_save():
    table_names, descriptions = load_schema()
    print(f"Embedding {len(descriptions)} table descriptions...")
    embeddings = get_embeddings(descriptions)

    with open(EMBED_PATH, "wb") as f:
        pickle.dump((embeddings, table_names, descriptions), f)

    print(f"✅ Saved embeddings to {EMBED_PATH}")

# Step 4: Load and retrieve schema context by user question
def get_schema_context(query, top_k=5):
    with open(EMBED_PATH, "rb") as f:
        embeddings, table_names, descriptions = pickle.load(f)

    query_embedding = get_embeddings([query])[0]  # single embedding

    knn = NearestNeighbors(n_neighbors=top_k, metric="cosine")
    knn.fit(embeddings)

    distances, indices = knn.kneighbors([query_embedding])
    return [descriptions[i] for i in indices[0]]

# Run as CLI
if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2 and sys.argv[1] == "embed":
        embed_and_save()

    elif len(sys.argv) > 2 and sys.argv[1] == "ask":
        question = " ".join(sys.argv[2:])
        print("\n📎 Relevant schema context:")
        for item in get_schema_context(question):
            print("-", item)

    else:
        print("Usage:")
        print("  python schema_rag_nomic.py embed        # Build and save schema embeddings")
        print("  python schema_rag_nomic.py ask <query>  # Get relevant schema for a question")
