# Loads FAISS index and handles all similarity searches

import json
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from core.builder import build_movie_document, is_hidden_gem, format_movie_card

# Constant
FAISS_INDEX_PATH = "faiss.index"
METADATA_PATH    = "faiss_metadata.json"
ENRICHED_PATH    = "data/movies_enriched.json"
MODEL_NAME       = "all-MiniLM-L6-v2"

# Load model + index (cached by streamlit)
def load_resources():
    """
    Loads:
    1. Sentence transformer model for embedding queries
    2. FAISS index for similarity search
    3. Metadata list for retrieving movie details

    Call this once at app startup via st.cache_resource.
    """

    if not os.path.exists(FAISS_INDEX_PATH):
        raise FileNotFoundError(
            "faiss.index not found - run data/embed.py first"
        )
    if not os.path.exists(METADATA_PATH):
        raise FileNotFoundError(
            "faiss_metadata.json not found - run data/embed.py first"
        )
    
    model    = SentenceTransformer(MODEL_NAME)
    index    = faiss.read_index(FAISS_INDEX_PATH)

    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    return model, index, metadata

# Sanitise user input
def sanitise_query(query: str, max_length: int = 500) -> str:
    """
    Strips dangerous characters and caps query length.
    Prevents prompt injection and oversized inputs.
    """
    import re
    if not isinstance(query, str):
        return ""
    query = re.sub(r"[<>{}\[\]\\]", "", query)
    return query.strip()[:max_length]

# Core retrieval
def retrieve(
    query: str,
    model: SentenceTransformer,
    index: faiss.Index,
    metadata: list,
    top_k: int = 5,
    filter_gems: bool = False,
) -> list[dict]:
    """
    Main retrieval function.
    1. Embeds the query
    2. Searches FAISS for nearest neighbours
    3. Returns top_k movie cards

    filter_gems=True → only returns hidden gems
    """
    query = sanitise_query(query)
    if not query:
        return []
    
    # Embed query — must match dimensions of index
    query_vector = model.encode([query], normalize_embeddings=True)
    query_vector = np.array(query_vector, dtype=np.float32)

    # Search FAISS — returns distances and indices
    # Search more than top_k so we have room to filter
    search_k = top_k * 4 if filter_gems else top_k * 2
    distances, indices = index.search(query_vector, search_k)

    results = []
    for idx in indices[0]:
        if idx == -1:
            continue
        movie = metadata[idx]

        # Apply hidden gem filter if requested
        if filter_gems and not is_hidden_gem(movie):
            continue

        results.append(format_movie_card(movie))

        if len(results) >= top_k:
            break

    return results

# Title search
def search_by_title(
    title: str,
    metadata: list,
    threshold: int = 60,
) -> dict | None:
    """
    Finds a movie by title for Deep Dive mode.
    Uses fuzzy matching so "parasite" matches "Parasite".
    Returns the best match or None.
    """
    title = sanitise_query(title).lower().strip()
    if not title:
        return None

    best_match = None
    best_score = 0

    for movie in metadata:
        movie_title = movie.get("title", "").lower().strip()

        # Exact match — return immediately
        if movie_title == title:
            return format_movie_card(movie)

        # Partial match scoring
        if title in movie_title or movie_title in title:
            score = len(title) / max(len(movie_title), 1) * 100
            if score > best_score:
                best_score = score
                best_match = movie

    if best_match and best_score >= threshold:
        return format_movie_card(best_match)

    return None