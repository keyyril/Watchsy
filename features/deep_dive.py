# Deep dive mode — detailed breakdown of a single film

import streamlit as st
from core.retriever import search_by_title
from core.llm import get_deep_dive


def render(model, index, metadata):
    st.header("🔍 Deep Dive")
    st.write("Get a rich breakdown of any film — themes, style, cultural context, and what to watch next.")

    # ── Build title list for autocomplete ─────────────────────────────────────
    all_titles = sorted([m.get("title", "") for m in metadata])

    # ── Search input with autocomplete ────────────────────────────────────────
    col1, col2 = st.columns([4, 1])

    with col1:
        title_query = st.selectbox(
            "Search for a film",
            options=[""] + all_titles,
            index=0,
            key="deep_dive_input",
            placeholder="Type to search...",
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        search_clicked = st.button(
            "🔍 Search",
            type="primary",
            use_container_width=True,
        )

    # ── Popular deep dives ────────────────────────────────────────────────────
    st.markdown("**Popular deep dives:**")
    suggestions = [
        "Parasite", "Inception", "The Godfather",
        "Spirited Away", "No Country for Old Men"
    ]

    cols = st.columns(5)
    for i, suggestion in enumerate(suggestions):
        with cols[i]:
            if st.button(suggestion, key=f"suggestion_{i}"):
                st.session_state.deep_dive_query = suggestion
                st.session_state.current_movie = None
                st.session_state.current_deep_dive = None
                st.rerun()

    st.divider()

    # ── Handle search ─────────────────────────────────────────────────────────
    active_query = st.session_state.get("deep_dive_query", title_query)

    if search_clicked and title_query.strip():
        with st.spinner(f"Searching for '{title_query}'..."):
            movie = search_by_title(title_query, metadata)

        if not movie:
            st.error(f"Couldn't find '{title_query}' in our database.")
            st.info("💡 Try a slightly different spelling, or this film may not be in our corpus yet.")
            return

        st.session_state.current_movie = movie
        st.session_state.current_deep_dive = None
        st.session_state.deep_dive_query = title_query
        st.rerun()

    # ── Handle suggestion buttons ─────────────────────────────────────────────
    suggestion_query = st.session_state.get("deep_dive_query")
    if suggestion_query and not st.session_state.get("current_movie"):
        with st.spinner(f"Searching for '{suggestion_query}'..."):
            movie = search_by_title(suggestion_query, metadata)

        if not movie:
            st.error(f"Couldn't find '{suggestion_query}' in our database.")
            return

        st.session_state.current_movie = movie
        st.session_state.current_deep_dive = None
        st.rerun()

    # ── Display movie if one is loaded ────────────────────────────────────────
    movie = st.session_state.get("current_movie")
    if not movie:
        return

    # ── Movie header ──────────────────────────────────────────────────────────
    col1, col2 = st.columns([1, 3])

    with col1:
        if movie.get("poster"):
            poster_url = f"https://image.tmdb.org/t/p/w300{movie['poster']}"
            st.image(poster_url, width=180)

    with col2:
        st.title(f"{movie['title']} ({movie['year']})")
        st.write(f"**Director:** {movie.get('director', 'Unknown')}")
        st.write(f"**Cast:** {', '.join(movie.get('cast', []))}")
        st.write(f"**Genres:** {', '.join(movie.get('genres', []))}")

        rating = movie.get("rating", 0)
        stars = "⭐" * int(rating / 2)
        st.write(f"**Rating:** {stars} {rating}/10")

        if movie.get("streaming"):
            st.write(f"**Streaming:** {', '.join(movie.get('streaming', []))}")

        if movie.get("themes"):
            theme_tags = " ".join([f"`{t}`" for t in movie.get("themes", [])])
            st.markdown(f"**Themes:** {theme_tags}")

    st.markdown(f"*{movie.get('overview', '')}*")
    st.divider()

    # ── Generate deep dive ────────────────────────────────────────────────────
    if not st.session_state.get("current_deep_dive"):
        with st.spinner("Generating deep dive analysis..."):
            deep_dive_text = get_deep_dive(movie)
        st.session_state.current_deep_dive = deep_dive_text

    st.subheader("📖 Deep Dive Analysis")
    st.markdown(st.session_state.current_deep_dive)