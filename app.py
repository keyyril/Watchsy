# Main Streamlit entry point — wires all features together

import streamlit as st
from core.retriever import load_resources
from core.llm import MAX_REQUESTS_PER_SESSION
from features import recommend, hidden_gems, deep_dive

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Watchsy",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #e50914, #ff6b6b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .sub-header {
        color: #888;
        font-size: 1rem;
        margin-top: 0;
    }
    .stButton > button {
        border-radius: 8px;
    }
    .stExpander {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ── Load resources once ───────────────────────────────────────────────────────
@st.cache_resource
def load_all_resources():
    """
    Loads FAISS index, metadata and embedding model once.
    Cached by Streamlit — never reloads on user interaction.
    """
    return load_resources()


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<p class="main-header">🎬 Watchsy</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">AI-powered movie recommendations</p>',
            unsafe_allow_html=True)
st.divider()

# ── Load resources ────────────────────────────────────────────────────────────
with st.spinner("Loading Watchsy..."):
    try:
        model, index, metadata = load_all_resources()
    except FileNotFoundError as e:
        st.error(f"⚠️ Setup required: {e}")
        st.info("Run these commands first:\n```\npython data/enrich.py\npython data/embed.py\n```")
        st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎬 Watchsy")
    st.caption("AI-powered movie discovery")
    st.divider()

    mode = st.radio(
        "Choose a feature",
        ["🎬 Recommend", "💎 Hidden Gems", "🔍 Deep Dive"],
        key="mode_selector",
    )

    st.divider()

    # ── Stats ─────────────────────────────────────────────────────────────────
    st.markdown("### 📊 Database")
    st.metric("Movies indexed", f"{len(metadata):,}")

    st.divider()

    # ── Session usage ─────────────────────────────────────────────────────────
    request_count = st.session_state.get("request_count", 0)
    remaining = max(0, MAX_REQUESTS_PER_SESSION - request_count)

    st.markdown("### 🔋 Session Usage")
    st.progress(request_count / MAX_REQUESTS_PER_SESSION)
    st.caption(f"{request_count}/{MAX_REQUESTS_PER_SESSION} requests used")

    if remaining <= 3:
        st.warning(f"⚠️ {remaining} requests left")
    else:
        st.caption(f"✅ {remaining} requests remaining")

    st.divider()
    st.caption("Built with TMDB + Groq + FAISS")
    st.caption("Data: The Movie Database (TMDB)")

# ── Route to feature ──────────────────────────────────────────────────────────
if mode == "🎬 Recommend":
    recommend.render(model, index, metadata)

elif mode == "💎 Hidden Gems":
    hidden_gems.render(model, index, metadata)

elif mode == "🔍 Deep Dive":
    deep_dive.render(model, index, metadata)