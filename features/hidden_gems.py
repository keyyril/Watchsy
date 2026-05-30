# Hidden gems finder feature

import streamlit as st
from core.retriever import retrieve
from core.llm import get_hidden_gems


def render(model, index, metadata):
    st.header("💎 Hidden Gems")
    st.write("Discover underseen films that deserve way more attention.")

    # ── What counts as a hidden gem ───────────────────────────────────────────
    with st.expander("ℹ️ What counts as a hidden gem?"):
        st.markdown("""
        We define a hidden gem as a film that is:
        - ⭐ Rated **7.5 or higher** on TMDB
        - 👤 Has a **popularity score under 30** (most blockbusters score 100+)
        - 🗳️ Has at least **100 votes** (so it's credible, not just 5 friends)
        
        These are films that critics and cinephiles love but mainstream 
        audiences haven't discovered yet.
        """)

    # ── Example prompts ───────────────────────────────────────────────────────
    st.markdown("**Try something like:**")
    examples = [
        "Underseen psychological thrillers from the 90s",
        "Hidden gem sci-fi films that make you think",
        "Overlooked foreign language dramas",
        "Underrated dark comedies",
        "Hidden gem action films with great storytelling",
    ]

    cols = st.columns(2)
    for i, example in enumerate(examples):
        with cols[i % 2]:
            if st.button(example, key=f"gem_example_{i}"):
                st.session_state.gems_query = example

    st.divider()

    # ── Query input ───────────────────────────────────────────────────────────
    query = st.text_area(
        "What kind of hidden gem are you looking for?",
        value=st.session_state.get("gems_query", ""),
        placeholder="e.g. Slow burn thrillers with great atmosphere...",
        height=100,
        max_chars=500,
        key="gems_input",
    )

    # ── Filters ───────────────────────────────────────────────────────────────
    st.markdown("**Filters:**")
    col1, col2 = st.columns(2)

    with col1:
        min_rating = st.slider(
            "Minimum rating",
            min_value=7.0,
            max_value=9.0,
            value=7.5,
            step=0.1,
        )

    with col2:
        decade = st.selectbox(
            "Decade (optional)",
            ["Any", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
        )

    if st.button("💎 Find Hidden Gems", type="primary", use_container_width=True):
        if not query.strip():
            st.warning("Please describe what kind of hidden gem you're after.")
            return

        # ── Retrieve candidates ───────────────────────────────────────────────
        with st.spinner("Searching for overlooked films..."):
            candidates = retrieve(
                query=query,
                model=model,
                index=index,
                metadata=metadata,
                top_k=8,
                filter_gems=True,
            )

        # ── Apply additional filters ──────────────────────────────────────────
        if min_rating > 7.5:
            candidates = [m for m in candidates if m.get("rating", 0) >= min_rating]

        if decade != "Any":
            decade_map = {
                "1960s": ("1960", "1969"),
                "1970s": ("1970", "1979"),
                "1980s": ("1980", "1989"),
                "1990s": ("1990", "1999"),
                "2000s": ("2000", "2009"),
                "2010s": ("2010", "2019"),
                "2020s": ("2020", "2029"),
            }
            start, end = decade_map[decade]
            candidates = [
                m for m in candidates
                if start <= m.get("year", "0000") <= end
            ]

        if not candidates:
            st.warning("No hidden gems found matching your filters. Try relaxing the criteria.")
            return

        # ── Generate LLM response ─────────────────────────────────────────────
        with st.spinner("Curating your hidden gems..."):
            response = get_hidden_gems(query, candidates)

        # ── Display results ───────────────────────────────────────────────────
        st.subheader("💎 Your Hidden Gems")
        st.markdown(response)

        st.divider()

        # ── Gem cards ─────────────────────────────────────────────────────────
        st.subheader(f"📋 {len(candidates)} Hidden Gems Found")

        for movie in candidates:
            with st.expander(f"💎 {movie['title']} ({movie['year']}) — ⭐ {movie['rating']}/10"):
                col1, col2 = st.columns([1, 3])

                with col1:
                    if movie.get("poster"):
                        poster_url = f"https://image.tmdb.org/t/p/w200{movie['poster']}"
                        st.image(poster_url, width=120)

                with col2:
                    st.write(f"**Director:** {movie.get('director', 'Unknown')}")
                    st.write(f"**Genres:** {', '.join(movie.get('genres', []))}")
                    st.write(f"**Popularity Score:** {movie.get('popularity', 0):.1f} (lower = more obscure)")
                    if movie.get("themes"):
                        st.write(f"**Themes:** {', '.join(movie.get('themes', []))}")
                    if movie.get("tone"):
                        st.write(f"**Tone:** {movie.get('tone')}")
                    if movie.get("streaming"):
                        st.write(f"**Streaming:** {', '.join(movie.get('streaming', []))}")
                    st.write(movie.get("overview", "")[:200] + "...")