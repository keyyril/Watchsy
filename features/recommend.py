# Vibe-based movie recommender feature

import streamlit as st
from core.retriever import retrieve
from core.llm import get_recommendation


def render(model, index, metadata):
    st.header("🎬 Find Your Next Film")
    st.write("Describe the vibe, mood, or type of film you're looking for.")

    # ── Example prompts ───────────────────────────────────────────────────────
    st.markdown("**Try something like:**")
    examples = [
        "Something like Parasite but set in America",
        "A slow burn psychological thriller with an unreliable narrator",
        "Feel-good movies about friendship and second chances",
        "Dark sci-fi that makes you question reality",
        "A visually stunning film with minimal dialogue",
    ]

    cols = st.columns(2)
    for i, example in enumerate(examples):
        with cols[i % 2]:
            if st.button(example, key=f"example_{i}"):
                st.session_state.recommend_query = example

    st.divider()

    # ── Query input ───────────────────────────────────────────────────────────
    query = st.text_area(
        "What are you in the mood for?",
        value=st.session_state.get("recommend_query", ""),
        placeholder="e.g. A dark comedy about class divide with great cinematography...",
        height=100,
        max_chars=500,
        key="recommend_input",
    )

    if st.button("🔍 Find Films", type="primary", use_container_width=True):
        if not query.strip():
            st.warning("Please describe what you're looking for.")
            return

        # ── Retrieve candidates ───────────────────────────────────────────────
        with st.spinner("Searching through films..."):
            candidates = retrieve(
                query=query,
                model=model,
                index=index,
                metadata=metadata,
                top_k=5,
                filter_gems=False,
            )

        if not candidates:
            st.error("No matches found. Try a different description.")
            return

        # ── Generate LLM recommendation ───────────────────────────────────────
        with st.spinner("Curating your recommendations..."):
            recommendation = get_recommendation(query, candidates)

        # ── Display results ───────────────────────────────────────────────────
        st.subheader("🎯 Recommended For You")
        st.markdown(recommendation)

        st.divider()

        # ── Show movie cards ──────────────────────────────────────────────────
        st.subheader("📋 Films Considered")
        st.caption("All films our system retrieved and evaluated for your query")

        for movie in candidates:
            with st.expander(f"{movie['title']} ({movie['year']}) — ⭐ {movie['rating']}/10"):
                col1, col2 = st.columns([1, 3])

                with col1:
                    if movie.get("poster"):
                        poster_url = f"https://image.tmdb.org/t/p/w200{movie['poster']}"
                        st.image(poster_url, width=120)

                with col2:
                    st.write(f"**Director:** {movie.get('director', 'Unknown')}")
                    st.write(f"**Genres:** {', '.join(movie.get('genres', []))}")
                    if movie.get("themes"):
                        st.write(f"**Themes:** {', '.join(movie.get('themes', []))}")
                    if movie.get("tone"):
                        st.write(f"**Tone:** {movie.get('tone')}")
                    if movie.get("streaming"):
                        st.write(f"**Streaming:** {', '.join(movie.get('streaming', []))}")
                    st.write(movie.get("overview", "")[:200] + "...")

        # ── Save to session state ─────────────────────────────────────────────
        st.session_state.last_recommendation = recommendation
        st.session_state.last_candidates = candidates