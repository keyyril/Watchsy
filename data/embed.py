# Builds FAISS index from enriched movies
# Run once locally — generates faiss.index and faiss_metadata.json

import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from core.builder import build_movie_document

# ── Constants ─────────────────────────────────────────────────────────────────
ENRICHED_PATH    = "data/movies_enriched.json"
FAISS_INDEX_PATH = "faiss.index"
METADATA_PATH    = "faiss_metadata.json"
MODEL_NAME       = "all-MiniLM-L6-v2"


def main():
    print("Watchsy — Building FAISS index\n")

    # ── Load enriched movies ──────────────────────────────────────────────────
    if not os.path.exists(ENRICHED_PATH):
        raise FileNotFoundError(
            f"{ENRICHED_PATH} not found — run data/enrich.py first"
        )

    with open(ENRICHED_PATH, "r", encoding="utf-8") as f:
        movies = json.load(f)

    print(f"  ✓ Loaded {len(movies)} enriched movies")

    # ── Build documents ───────────────────────────────────────────────────────
    print("Building documents...")
    documents = []
    valid_movies = []

    for movie in movies:
        doc = build_movie_document(movie)
        if doc.strip():
            documents.append(doc)
            valid_movies.append(movie)

    print(f"  ✓ Built {len(documents)} documents")

    # ── Load embedding model ──────────────────────────────────────────────────
    print("\nLoading sentence transformer model...")
    model = SentenceTransformer(MODEL_NAME)
    print(f"  ✓ Model loaded: {MODEL_NAME}")

    # ── Generate embeddings ───────────────────────────────────────────────────
    print("\nGenerating embeddings (this may take a few minutes)...")
    embeddings = model.encode(
        documents,
        normalize_embeddings=True,   # normalise for cosine similarity
        show_progress_bar=True,
        batch_size=64,
    )

    embeddings = np.array(embeddings, dtype=np.float32)
    print(f"Generated embeddings shape: {embeddings.shape}")

    # ── Build FAISS index ─────────────────────────────────────────────────────
    print("\nBuilding FAISS index...")
    dimension = embeddings.shape[1]

    # IndexFlatIP = inner product (cosine similarity with normalised vectors)
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    print(f"Index built — {index.ntotal} vectors, {dimension} dimensions")

    # ── Save index + metadata ─────────────────────────────────────────────────
    print("\nSaving files...")

    faiss.write_index(index, FAISS_INDEX_PATH)
    print(f"Saved {FAISS_INDEX_PATH}")

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(valid_movies, f, ensure_ascii=False, indent=2)
    print(f"Saved {METADATA_PATH}")

    # ── Verify ────────────────────────────────────────────────────────────────
    print("\nVerifying index...")
    test_query = "dark psychological thriller"
    test_vector = model.encode([test_query], normalize_embeddings=True)
    test_vector = np.array(test_vector, dtype=np.float32)
    distances, indices = index.search(test_vector, 3)

    print(f"  Test query: '{test_query}'")
    print(f"  Top 3 results:")
    for i, idx in enumerate(indices[0]):
        title = valid_movies[idx].get("title", "Unknown")
        year  = valid_movies[idx].get("year", "")
        print(f"    {i+1}. {title} ({year}) — score: {distances[0][i]:.4f}")

    print(f"\nDone — FAISS index ready with {index.ntotal} movies")


if __name__ == "__main__":
    main()