# All Groq API calls — one function per feature

import os
import re
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

try:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
except Exception:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise EnvironmentError("GROQ_API_KEY not found")

client = Groq(api_key=GROQ_API_KEY)
MODEL  = "llama-3.1-8b-instant"
MAX_REQUESTS_PER_SESSION = 10


# ── Session limit ─────────────────────────────────────────────────────────────
def check_session_limit() -> bool:
    if "request_count" not in st.session_state:
        st.session_state.request_count = 0
    st.session_state.request_count += 1
    return st.session_state.request_count <= MAX_REQUESTS_PER_SESSION


# ── Sanitise before sending to LLM ───────────────────────────────────────────
def sanitise_input(text: str, max_length: int = 500) -> str:
    if not isinstance(text, str):
        return ""
    text = re.sub(r"[<>{}\[\]\\]", "", text)
    return text.strip()[:max_length]


def format_candidates(movies: list[dict]) -> str:
    """Formats retrieved movies into a readable block for the prompt."""
    lines = []
    for i, m in enumerate(movies, 1):
        genres   = ", ".join(m.get("genres", []))
        themes   = ", ".join(m.get("themes", []))
        tone     = m.get("tone", "")
        rating   = m.get("rating", 0)
        year     = m.get("year", "")
        director = m.get("director", "")
        overview = m.get("overview", "")[:200]

        lines.append(f"""
{i}. {m['title']} ({year}) — Dir. {director}
   Genres: {genres}
   Themes: {themes}
   Tone: {tone}
   Rating: {rating}/10
   Overview: {overview}...""")

    return "\n".join(lines)


# ── Feature 1 — Vibe Recommender ─────────────────────────────────────────────
def get_recommendation(user_query: str, candidates: list[dict]) -> str:
    if not check_session_limit():
        return "Session limit reached — please refresh the page."

    user_query = sanitise_input(user_query)

    system_prompt = """You are a world-class film curator with deep knowledge 
of cinema history, themes, and directing styles. 

Your job is to recommend films that genuinely match what the user is looking for.
Be specific — reference themes, tone, pacing, and emotional experience.
Never be generic. Write like a knowledgeable film-loving friend, not a database.
Keep each recommendation to 3-4 sentences."""

    user_prompt = f"""User is looking for: "{user_query}"

Here are candidate films retrieved from our database:
{format_candidates(candidates)}

From these candidates, recommend the 2-3 best matches.
For each film explain specifically WHY it matches the user's request.
Reference the themes, tone, and emotional experience — not just the plot.
If a film is a particularly surprising or non-obvious match, highlight that.

Format your response as:
🎬 [Film Title] ([Year])
[Your recommendation reasoning]

Then after all recommendations, add one line:
💡 Also consider: [1-2 other titles from the list that are worth mentioning]"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=600,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Sorry, I couldn't generate recommendations right now. Error: {e}"


# ── Feature 2 — Hidden Gems ───────────────────────────────────────────────────
def get_hidden_gems(user_query: str, candidates: list[dict]) -> str:
    if not check_session_limit():
        return "Session limit reached — please refresh the page."

    user_query = sanitise_input(user_query)

    system_prompt = """You are a passionate cinephile who specialises in 
discovering overlooked and underseen films.

Your job is to help users find hidden gems — films that are genuinely great
but flew under the radar. Be enthusiastic but specific. Explain what makes
each film special and why it deserves more attention.
Write like someone who just watched a great film and can't stop talking about it."""

    user_prompt = f"""User is looking for hidden gems matching: "{user_query}"

These are underseen films retrieved from our database (all have high ratings but low popularity):
{format_candidates(candidates)}

Recommend the 2-3 best hidden gems from this list.
For each film:
- Explain what makes it special and underrated
- Why it matches what the user is looking for  
- What kind of viewer would love it most
- Why it deserves more attention than it gets

Format your response as:
💎 [Film Title] ([Year])
[Your recommendation reasoning]

End with:
🎯 Best for: [one sentence describing the ideal viewer for these picks]"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=600,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Sorry, I couldn't find hidden gems right now. Error: {e}"


# ── Feature 3 — Deep Dive ─────────────────────────────────────────────────────
def get_deep_dive(movie: dict) -> str:
    if not check_session_limit():
        return "Session limit reached — please refresh the page."

    title    = sanitise_input(movie.get("title", ""))
    year     = movie.get("year", "")
    director = sanitise_input(movie.get("director", ""))
    overview = sanitise_input(movie.get("overview", ""), max_length=500)
    genres   = ", ".join(movie.get("genres", []))
    themes   = ", ".join(movie.get("themes", []))
    tone     = sanitise_input(movie.get("tone", ""))
    cast     = ", ".join(movie.get("cast", []))
    rating   = movie.get("rating", 0)

    system_prompt = """You are an insightful film critic and cultural analyst.
Your deep dives are engaging, intelligent, and accessible — not academic.
You connect films to broader themes, cultural moments, and human experiences.
Write like you're having a fascinating conversation about a film you love."""

    user_prompt = f"""Give me a deep dive on this film:

Title: {title} ({year})
Director: {director}
Cast: {cast}
Genres: {genres}
Themes: {themes}
Tone: {tone}
Rating: {rating}/10
Overview: {overview}

Structure your deep dive as:

🎭 What It's Really About
[The deeper themes and what the film is saying beneath the surface]

🎨 Style & Tone  
[The director's approach, visual style, pacing, atmosphere]

🌍 Why It Matters
[Cultural context, impact, what makes it significant]

❤️ Who Will Love It
[Specific types of viewers who will connect with this film]

🎬 Watch Next
[2-3 specific film recommendations if you loved this one, with one sentence each]"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=1024,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Sorry, I couldn't generate a deep dive right now. Error: {e}"