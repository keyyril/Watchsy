import json
import os
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError("GROQ_API_KEY not found in .env file")

client = Groq(api_key=GROQ_API_KEY)

# ── Ask Groq to enrich one movie ──────────────────────────────────────────────
def enrich_movie(movie: dict) -> dict:
    prompt = f"""Analyze this movie and return ONLY a JSON object, no explanation, no markdown, no backticks.

Movie: {movie['title']} ({movie['year']})
Director: {movie['director']}
Genres: {', '.join(movie['genres'])}
Keywords: {', '.join(movie['keywords'])}
Overview: {movie['overview']}

Return exactly this JSON structure:
{{
  "themes": ["theme1", "theme2", "theme3"],
  "tone": "one sentence describing the emotional tone",
  "mood": ["mood1", "mood2"],
  "pace": "slow burn / moderate / fast paced",
  "audience": "who would enjoy this film",
  "similar_vibes": ["vibe1", "vibe2", "vibe3"]
}}"""

    try:
        response = client.chat.completions.create(
            model = "llama-3.1-8b-instant",
            messages = [{"role": "user", "content": prompt}],
            max_tokens = 300,
            temperature = 0.3,
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown backticks if model adds them
        raw = raw.replace("```json", "").replace("```", "").strip()

        enriched = json.loads(raw)
        movie.update(enriched)
        return movie

    except json.JSONDecodeError:
        print(f"  ⚠ JSON parse error for {movie['title']} — skipping enrichment")
        return movie
    except Exception as e:
        print(f"  ⚠ Groq error for {movie['title']}: {e}")
        time.sleep(5)  # back off on error
        return movie


def main():
    import sys
    fix_mode = "--fix" in sys.argv

    print("✨ Watchsy — Enriching movies with Groq\n")

    input_path  = "data/movies.json"
    output_path = "data/movies_enriched.json"

    with open(input_path, "r", encoding="utf-8") as f:
        movies = json.load(f)

    # ── Fix mode — only re-enrich movies missing themes(python data/enrich.py --fix)───────────────────────
    if fix_mode:
        if not os.path.exists(output_path):
            print("  ⚠ No enriched file found — run normally first")
            return

        with open(output_path, "r", encoding="utf-8") as f:
            enriched_movies = json.load(f)

        # Find indices of movies missing themes
        missing = [i for i, m in enumerate(enriched_movies) if not m.get("themes")]
        print(f"  🔧 Fix mode — {len(missing)} movies missing enrichment\n")

        for i, idx in enumerate(missing):
            movie = enriched_movies[idx]
            print(f"  Fixing: {movie['title']}")
            enriched = enrich_movie(movie)
            enriched_movies[idx] = enriched
            time.sleep(2.1)

            if (i + 1) % 10 == 0:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(enriched_movies, f, ensure_ascii=False, indent=2)
                print(f"  💾 Saved fixes ({i+1}/{len(missing)})")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(enriched_movies, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Fixed {len(missing)} movies")
        return

    # ── Normal mode — resume from where we left off ───────────────────────────
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            enriched_movies = json.load(f)
        enriched_ids = {m["id"] for m in enriched_movies}
        to_enrich = [m for m in movies if m["id"] not in enriched_ids]
        print(f"  ↩ Resuming — {len(enriched_movies)} done, {len(to_enrich)} remaining\n")
    else:
        enriched_movies = []
        to_enrich = movies[:1000]
        print(f"  Starting fresh — {len(to_enrich)} movies to enrich\n")

    for i, movie in enumerate(to_enrich):
        enriched = enrich_movie(movie)
        enriched_movies.append(enriched)

        if (i + 1) % 50 == 0:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(enriched_movies, f, ensure_ascii=False, indent=2)
            print(f"  💾 Saved {len(enriched_movies)} enriched ({i+1}/{len(to_enrich)} processed)")

        time.sleep(2.1)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched_movies, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Done — {len(enriched_movies)} enriched movies saved to data/movies_enriched.json")


if __name__ == "__main__":
    main()