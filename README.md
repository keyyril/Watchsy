# 🎬 Watchsy — AI-Powered Movie Discovery

> Describe a vibe. Discover a film.

Watchsy is a full-stack RAG (Retrieval-Augmented Generation) application that lets users find movies through natural language — not keyword search. Built with TMDB, Groq LLaMA, FAISS, and Streamlit.

**Live app:** [watchsy.streamlit.app](https://your-watchsy-url.streamlit.app)

---

## Features

**🎬 Vibe-Based Recommender**
Describe what you're in the mood for in plain English — *"something like Parasite but set in America"* — and get curated recommendations with specific reasoning about why each film fits.

**💎 Hidden Gems Finder**
Discover underseen films with high ratings but low popularity scores. Filter by decade and minimum rating. The app surfaces films that deserve more attention than they get.

**🔍 Deep Dive Analysis**
Search any film in the corpus and get a structured breakdown — themes, directing style, cultural context, who will love it, and what to watch next.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Data Source | TMDB API |
| LLM Enrichment | Groq (llama-3.1-8b-instant) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector Store | FAISS (IndexFlatIP) |
| LLM Inference | Groq (llama-3.3-70b-versatile) |
| Frontend | Streamlit |

---

## How It Works

```
User types: "slow burn psychological thriller with an unreliable narrator"
        ↓
Query embedded into 384-dim vector (sentence-transformers)
        ↓
FAISS searches 5,000 movie vectors for closest semantic matches
        ↓
Top 5 candidates retrieved with full metadata
        ↓
Groq LLM reasons over candidates → picks best 2-3 with explanation
        ↓
Results displayed with posters, themes, streaming info
```

The key insight: movies are embedded using **Groq-enriched documents** — not just TMDB overviews. Each film has LLM-generated themes, tone, mood, and audience metadata added before embedding, which dramatically improves retrieval quality.

---

## Project Structure

```
Watchsy/
│
├── app.py                  # Streamlit entry point, routing
│
├── data/
│   ├── fetch_tmdb.py       # Fetches 5,000 movies from TMDB API
│   ├── enrich.py           # Uses Groq to add themes/tone per film
│   └── embed.py            # Builds FAISS index from enriched data
│
├── core/
│   ├── builder.py          # Builds rich text documents for embedding
│   ├── retriever.py        # FAISS search + title lookup
│   └── llm.py              # All Groq API calls, one per feature
│
├── features/
│   ├── recommend.py        # Vibe-based recommender UI
│   ├── hidden_gems.py      # Hidden gems finder UI
│   └── deep_dive.py        # Deep dive analysis UI
│
├── faiss.index             # Pre-built vector index (5,000 films)
├── faiss_metadata.json     # Movie metadata alongside index
├── requirements.txt
└── packages.txt
```

---

## Local Setup

**1. Clone the repo**
```bash
git clone https://github.com/keyyril/Watchsy.git
cd Watchsy
```

**2. Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Add API keys**

Create a `.env` file in the root:
```env
TMDB_API_KEY="your_tmdb_key"
GROQ_API_KEY="your_groq_key"
```

Get your keys:
- **TMDB** → [themoviedb.org](https://www.themoviedb.org/settings/api) → API → API Key (v3)
- **Groq** → [console.groq.com](https://console.groq.com) → API Keys → Create new key

**5. Run the app**
```bash
streamlit run app.py
```

> The FAISS index is pre-built and committed to the repo — no need to run the data pipeline scripts to use the app locally.

---

## Rebuilding the Corpus

To refresh or expand the movie database:

```bash
# Step 1 — Fetch movies from TMDB (resumes if interrupted)
python data/fetch_tmdb.py

# Step 2 — Enrich with Groq LLM (resumes if interrupted)
python data/enrich.py

# Step 3 — Rebuild FAISS index
python data/embed.py
```

> Groq free tier allows ~500k tokens/day per model. Rotate models in `enrich.py` to enrich all 5,000 films in one day without waiting for resets.

---

## Corpus

| Metric | Value |
|---|---|
| Total films | 5,000 |
| AI enriched | ~5,000 |
| Vector dimensions | 384 |
| Languages covered | English, Korean, Japanese, French, Spanish, Hindi, Italian, Chinese, German + more |
| Decades covered | 1950s — 2020s |

Films are stratified across popularity tiers, genres, decades, and languages — not randomly sampled — to ensure broad coverage of real user queries.

---

## Security

- API keys loaded from `.env` locally and Streamlit Secrets on cloud — never hardcoded
- All user inputs sanitised before embedding or LLM calls
- Session-based request limiting prevents token abuse on public deployment
- `.env` and `secrets.toml` are in `.gitignore`

---

## Deployment

Deployed on [Streamlit Community Cloud](https://share.streamlit.io). To deploy your own:

1. Fork this repo
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Select your fork, set main file to `app.py`
4. Add your API keys under Advanced Settings → Secrets:
```toml
TMDB_API_KEY = "your_key"
GROQ_API_KEY = "your_key"
```
5. Deploy

---

## License

MIT License — free to use, modify, and distribute.

---

*Built with [TMDB API](https://www.themoviedb.org/documentation/api) · [Groq](https://groq.com) · [FAISS](https://github.com/facebookresearch/faiss) · [Streamlit](https://streamlit.io)*
