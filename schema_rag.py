import json
import pickle
import requests
import re
from sklearn.neighbors import NearestNeighbors
from typing import Dict, List, Tuple

OLLAMA_URL = "http://localhost:11434/api/embeddings"
MODEL_NAME = "nomic-embed-text"
SCHEMA_PATH = "augur_schema.json"
TABLE_EMBED_PATH = "augur_table_embeddings.pkl"
COLUMN_EMBED_PATH = "augur_column_embeddings.pkl"

def infer_column_meaning(column_name: str, table_name: str) -> str:
    """Infer semantic meaning from column names - same as before"""
    col = column_name.lower()
    
    patterns = {
        # IDs and references
        r'.*_id$': 'unique identifier',
        r'repo_id': 'repository identifier',
        r'cntrb_id': 'contributor identifier',
        r'pull_request_id': 'pull request identifier',
        r'issue_id': 'issue identifier',
        
        # Timestamps and dates
        r'.*_at$': 'timestamp when event occurred',
        r'.*_date$': 'date when event occurred',
        r'created_at': 'creation timestamp',
        r'updated_at': 'last update timestamp',
        r'closed_at': 'closure timestamp',
        r'merged_at': 'merge timestamp',
        
        # Commit related
        r'cmt_.*hash': 'git commit hash identifier',
        r'cmt_author.*': 'commit author information',
        r'cmt_committer.*': 'commit committer information',
        r'cmt_added': 'lines of code added in commit',
        r'cmt_removed': 'lines of code removed in commit',
        r'cmt_.*email': 'email address of commit author/committer',
        r'cmt_.*name': 'name of commit author/committer',
        
        # Pull request related
        r'pr_.*state': 'pull request status (open/closed/merged)',
        r'pr_body': 'pull request description text',
        r'pr_.*title': 'pull request title',
        r'pr_src_number': 'pull request number on platform',
        r'pr_merged_at': 'timestamp when pull request was merged',
        
        # Issue related
        r'issue_title': 'issue title text',
        r'issue_body': 'issue description text',
        r'issue_state': 'issue status (open/closed)',
        r'gh_issue_number': 'GitHub issue number',
        
        # Repository related
        r'repo_name': 'repository name',
        r'fork_count': 'number of repository forks',
        r'stars_count': 'number of repository stars',
        r'watchers_count': 'number of repository watchers',
        r'open_issues': 'count of currently open issues',
        
        # Contributor related
        r'cntrb_login': 'contributor username/login',
        r'cntrb_email': 'contributor email address',
        r'cntrb_.*name': 'contributor name',
        r'cntrb_company': 'contributor company affiliation',
        
        # Counts and metrics
        r'.*_count$': 'count or number of items',
        r'comment_count': 'number of comments',
        r'total_lines': 'total lines of code',
        r'code_lines': 'lines containing code',
        
        # Meta fields (usually not relevant for queries)
        r'tool_source': 'data collection tool identifier',
        r'tool_version': 'version of data collection tool',
        r'data_source': 'source of the data',
        r'data_collection_date': 'when data was collected',
    }
    
    for pattern, description in patterns.items():
        if re.match(pattern, col):
            return description
    
    return f"{table_name} {column_name.replace('_', ' ')}"

def load_schema_for_tables():
    """Load table-level embeddings (your existing approach)"""
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)

    descriptions = []
    table_keys = []

    for table, metadata in schema.items():
        desc = metadata.get("description", "")
        # Just use description for table selection
        full_text = f"Table {table}: {desc}"
        descriptions.append(full_text)
        table_keys.append(table)

    return table_keys, descriptions

def load_schema_for_columns():
    """NEW: Load column-level embeddings"""
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)

    column_descriptions = []
    column_keys = []  # (table_name, column_name) tuples

    for table_name, metadata in schema.items():
        table_desc = metadata.get("description", "")
        columns = metadata.get("columns", [])
        
        for column_name in columns:
            # Create rich semantic description for each column
            column_meaning = infer_column_meaning(column_name, table_name)
            
            # Build contextual description for embedding
            full_desc = f"Column {column_name} in table {table_name}: {column_meaning}. Table context: {table_desc}"
            
            column_descriptions.append(full_desc)
            column_keys.append((table_name, column_name))

    return column_keys, column_descriptions

def get_embeddings(texts):
    """Your existing embedding function"""
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

def embed_and_save():
    """Embed both tables and columns separately"""
    print("Embedding tables...")
    table_keys, table_descriptions = load_schema_for_tables()
    table_embeddings = get_embeddings(table_descriptions)
    
    with open(TABLE_EMBED_PATH, "wb") as f:
        pickle.dump((table_embeddings, table_keys, table_descriptions), f)
    print(f"Saved table embeddings to {TABLE_EMBED_PATH}")
    
    print("Embedding columns...")
    column_keys, column_descriptions = load_schema_for_columns()
    column_embeddings = get_embeddings(column_descriptions)
    
    with open(COLUMN_EMBED_PATH, "wb") as f:
        pickle.dump((column_embeddings, column_keys, column_descriptions), f)
    print(f"Saved column embeddings to {COLUMN_EMBED_PATH}")

def get_relevant_tables(query: str, top_k: int = 5) -> List[str]:
    """Get relevant tables (your existing logic)"""
    with open(TABLE_EMBED_PATH, "rb") as f:
        embeddings, table_keys, descriptions = pickle.load(f)

    query_embedding = get_embeddings([query])[0]
    
    knn = NearestNeighbors(n_neighbors=min(top_k, len(embeddings)), metric="cosine")
    knn.fit(embeddings)
    
    distances, indices = knn.kneighbors([query_embedding])
    return [table_keys[i] for i in indices[0]]

def get_relevant_columns_for_tables(query: str, selected_tables: List[str], max_cols_per_table: int = 10) -> Dict[str, List[str]]:
    """NEW: Get relevant columns for selected tables"""
    with open(COLUMN_EMBED_PATH, "rb") as f:
        embeddings, column_keys, descriptions = pickle.load(f)

    query_embedding = get_embeddings([query])[0]
    
    # Filter to only columns from selected tables
    relevant_indices = []
    relevant_column_keys = []
    relevant_embeddings = []
    
    for i, (table_name, col_name) in enumerate(column_keys):
        if table_name in selected_tables:
            relevant_indices.append(i)
            relevant_column_keys.append((table_name, col_name))
            relevant_embeddings.append(embeddings[i])
    
    if not relevant_embeddings:
        return {}
    
    # Find most similar columns
    knn = NearestNeighbors(n_neighbors=len(relevant_embeddings), metric="cosine")
    knn.fit(relevant_embeddings)
    
    distances, indices = knn.kneighbors([query_embedding])
    
    # Group by table and limit
    result = {table: [] for table in selected_tables}
    table_counts = {table: 0 for table in selected_tables}
    
    for idx in indices[0]:
        table_name, col_name = relevant_column_keys[idx]
        if table_counts[table_name] < max_cols_per_table:
            result[table_name].append(col_name)
            table_counts[table_name] += 1
    
    return result

def get_essential_columns(table_name: str) -> List[str]:
    """Always include these essential columns"""
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)
    
    if table_name not in schema:
        return []
    
    columns = schema[table_name]['columns']
    essential = []
    
    # Always include IDs and timestamps
    for col in columns:
        col_lower = col.lower()
        if (col_lower.endswith('_id') or 
            col_lower in ['created_at', 'updated_at', 'closed_at', 'merged_at'] or
            'timestamp' in col_lower):
            essential.append(col)
    
    # Table-specific essentials
    table_essentials = {
        'commits': ['cmt_commit_hash', 'cmt_author_name', 'cmt_added', 'cmt_removed'],
        'pull_requests': ['pr_src_number', 'pr_src_title', 'pr_src_state'],
        'issues': ['issue_title', 'issue_state', 'gh_issue_number'],
        'contributors': ['cntrb_login', 'cntrb_full_name'],
        'repo': ['repo_name', 'repo_git'],
        'repo_info': ['stars_count', 'fork_count', 'open_issues']
    }
    
    if table_name in table_essentials:
        for essential_col in table_essentials[table_name]:
            if essential_col in columns and essential_col not in essential:
                essential.append(essential_col)
    
    return essential

def get_schema_context(query: str, top_tables: int = 5) -> str:
    """Build complete schema context with smart column selection"""
    # Step 1: Get relevant tables
    relevant_tables = get_relevant_tables(query, top_tables)
    
    # Step 2: Get relevant columns for those tables
    relevant_columns = get_relevant_columns_for_tables(query, relevant_tables)
    
    # Step 3: Build context
    context = "Database Schema Context:\n\n"
    
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)
    
    for table_name in relevant_tables:
        if table_name not in schema:
            continue
            
        table_desc = schema[table_name].get('description', '')
        context += f"## Table: {table_name}\n"
        if table_desc:
            context += f"Purpose: {table_desc}\n"
        
        # Get essential columns
        essential_cols = get_essential_columns(table_name)
        relevant_cols = relevant_columns.get(table_name, [])
        
        # Combine and deduplicate
        all_cols = list(dict.fromkeys(essential_cols + relevant_cols))
        
        context += "Columns:\n"
        for col in all_cols:
            col_meaning = infer_column_meaning(col, table_name)
            is_essential = col in essential_cols
            marker = " [ESSENTIAL]" if is_essential else ""
            context += f"  - {col}: {col_meaning}{marker}\n"
        
        context += "\n"
    
    return context

# CLI
if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2 and sys.argv[1] == "embed":
        embed_and_save()

    elif len(sys.argv) > 2 and sys.argv[1] == "ask":
        question = " ".join(sys.argv[2:])
        print("\nComplete Schema Context:")
        print(get_schema_context(question))

    else:
        print("Usage:")
        print("  python schema_rag.py embed        # Build and save schema embeddings")
        print("  python schema_rag.py ask <query>  # Get relevant schema for a question")