# core/builder.py
# Turns raw movie data into rich text documents for embedding

def build_movie_document(movie: dict) -> str:
    """
    Combines all movie fields into one rich text document.
    This is what gets embedded — richer = better retrieval.
    """

    # ── Basic fields ──────────────────────────────────────────────────────────
    title       = movie.get("title", "Unknown")
    year        = movie.get("year", "")
    director    = movie.get("director", "Unknown")
    overview    = movie.get("overview", "")
    tagline     = movie.get("tagline", "")
    runtime     = movie.get("runtime", 0)
    rating      = movie.get("rating", 0)
    language    = movie.get("original_language", "en")

    # ── List fields ───────────────────────────────────────────────────────────
    genres      = ", ".join(movie.get("genres", []))
    keywords    = ", ".join(movie.get("keywords", []))
    cast        = ", ".join(movie.get("cast", []))
    streaming   = ", ".join(movie.get("streaming", []))

    # ── Enriched fields (from enrich.py) ─────────────────────────────────────
    themes      = ", ".join(movie.get("themes", []))
    tone        = movie.get("tone", "")
    mood        = ", ".join(movie.get("mood", []))
    pace        = movie.get("pace", "")
    audience    = movie.get("audience", "")
    vibes       = ", ".join(movie.get("similar_vibes", []))

    # ── Build the document ────────────────────────────────────────────────────
    doc = f"""Title: {title} ({year})
Director: {director}
Cast: {cast}
Genres: {genres}
Keywords: {keywords}
Overview: {overview}
Tagline: {tagline}
Themes: {themes}
Tone: {tone}
Mood: {mood}
Pace: {pace}
Audience: {audience}
Similar Vibes: {vibes}
Runtime: {runtime} minutes
Rating: {rating}/10
Language: {language}
Streaming: {streaming}"""

    return doc.strip()


def build_hidden_gem_document(movie: dict) -> str:
    """
    Same as build_movie_document but adds a hidden gem flag.
    Used to bias retrieval toward underseen films.
    """
    base = build_movie_document(movie)
    return base + "\nStatus: Hidden Gem — highly rated but underseen"


def is_hidden_gem(movie: dict) -> bool:
    """
    Defines what counts as a hidden gem:
    - Good rating
    - Low popularity (underseen)
    - Enough votes to be credible
    """
    return (
        movie.get("rating", 0) >= 7.5
        and movie.get("popularity", 999) < 30
        and movie.get("vote_count", 0) >= 100
    )


def format_movie_card(movie: dict) -> dict:
    """
    Returns a clean dict for display in Streamlit UI.
    Only the fields the UI needs — nothing extra.
    """
    return {
        "id":         movie.get("id"),
        "title":      movie.get("title", "Unknown"),
        "year":       movie.get("year", ""),
        "director":   movie.get("director", "Unknown"),
        "genres":     movie.get("genres", []),
        "rating":     movie.get("rating", 0),
        "overview":   movie.get("overview", ""),
        "poster":     movie.get("poster_path"),
        "streaming":  movie.get("streaming", []),
        "themes":     movie.get("themes", []),
        "tone":       movie.get("tone", ""),
        "cast":       movie.get("cast", []),
    }