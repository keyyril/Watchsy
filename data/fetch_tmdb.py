import requests
import json
import time
import os
import re
from dotenv import load_dotenv

load_dotenv()

# Security: load from .env only, never hardcode
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
if not TMDB_API_KEY:
    raise EnvironmentError("TMDB_API_KEY not found in .env file")

BASE_URL = "https://api.themoviedb.org/3"
PARAMS_BASE = {"api_key": TMDB_API_KEY, "language": "en-US"}

# Input sanitisation
def sanitise_text(text: str, max_length: int = 2000) -> str:
    if not isinstance(text, str):
        return ""
    text = re.sub(r"[<>{}\[\]\\]", "", text)
    return text.strip()[:max_length]

# Fetch full deets for a moovie
def fetch_movie_details(movie_id: int) -> dict | None:
    try:
        r = requests.get(f"{BASE_URL}/movie/{movie_id}",
                         params= PARAMS_BASE, timeout= 10)
        r.raise_for_status()
        details = r.json()
        time.sleep(0.26)

        r = requests.get(f"{BASE_URL}/movie/{movie_id}/keywords",
                         params= PARAMS_BASE, timeout= 10)
        r.raise_for_status()
        keywords = [k["name"] for k in r.json().get ("keywords",  [])]
        time.sleep(0.26)

        r = requests.get(f"{BASE_URL}/movie/{movie_id}/credits",
                         params= PARAMS_BASE, timeout= 10)
        r.raise_for_status()
        credits = r.json()
        cast = [c["name"] for c in credits.get("cast", [])[:5]]
        director = next(
            (c["name"] for c in credits.get("crew",[])
             if c["job"] == "Director"), "Unknown"
        )
        time.sleep(0.26)

        r = requests.get(f"{BASE_URL}/movie/{movie_id}/watch/providers",
                         params= PARAMS_BASE, timeout= 10)
        r.raise_for_status()
        providers_data = r.json().get("results", {})
        region_data = providers_data.get("MY") or providers_data.get("US") or {}
        streaming = [p["provider_name"]
                     for p in region_data.get("flatrate",[])]
        time.sleep(0.26)

        return{
            "id": details.get("id"),
            "title": sanitise_text(details.get("title", "")),
            "year": (details.get("release_date") or "")[:4],
            "overview": sanitise_text(details.get("overview", "")),
            "genres": [g["name"] for g in details.get("genres", [])],
            "keywords": keywords[:15],
            "cast": cast,
            "director": sanitise_text(director),
            "rating": details.get("vote_average", 0),
            "vote_count": details.get("vote_count", 0),
            "popularity": details.get("popularity", 0),
            "poster_path": details.get("poster_path", 0),
            "streaming": streaming,
            "runtime": details.get("runtime", 0),
            "tagline": sanitise_text(details.get("tagline", "")),
            "original_language": details.get("original_language", "")
        }
    
    except requests.exceptions.RequestException as e:
        print(f"Network error for movie {movie_id}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error for movie {movie_id}: {e}")
        return None
    
# Discover movie ID by stratG
def discover_movies(params: dict, max_pages: int = 10) -> list:
    ids = []
    for page in range(1, max_pages + 1):
        try:
            r = requests.get(
                f"{BASE_URL}/discover/movie",
                params = {**PARAMS_BASE, **params, "page": page},
                timeout = 10
            )
            r.raise_for_status()
            results = r.json().get("results", [])
            if not results:
                break
            ids.extend([m["id"] for m in results])
            time.sleep(0.26)
        except requests.exceptions.RequestException as e:
            print(f"Discover error page {page}: {e}")
            break
    return ids

# Quality filter
def is_quality_movie(movie: dict) -> bool:
    return(
        len(movie.get("overview", "")) > 80
        and len(movie.get("keywords", [])) >= 2
        and movie.get("vote_count", 0) >= 50
        and movie.get("poster_path") is not None
        and len(movie.get("title", "")) > 0
    )

# Main
def main():
    print("🎬 Watchsy - Fetching movie corpus from TMDB\n")

    all_ids:set = set()

    strategies = [
        # Tier 1 — Most popular
        ({"sort_by": "popularity.desc"}, 50),

        # Tier 2 — Highly rated, well-voted
        ({"sort_by": "vote_average.desc", "vote_count.gte": 1000}, 40),

        # Tier 3 — Hidden gems
        ({"sort_by": "vote_average.desc", "vote_count.gte": 200,
          "vote_count.lte": 5000, "vote_average.gte": 7.5}, 30),

        # Tier 4 — By decade
        ({"sort_by": "popularity.desc", "primary_release_date.gte": "1950-01-01",
          "primary_release_date.lte": "1959-12-31", "vote_count.gte": 50}, 10),
        ({"sort_by": "popularity.desc", "primary_release_date.gte": "1960-01-01",
          "primary_release_date.lte": "1969-12-31", "vote_count.gte": 50}, 10),
        ({"sort_by": "popularity.desc", "primary_release_date.gte": "1970-01-01",
          "primary_release_date.lte": "1979-12-31", "vote_count.gte": 50}, 10),
        ({"sort_by": "popularity.desc", "primary_release_date.gte": "1980-01-01",
          "primary_release_date.lte": "1989-12-31", "vote_count.gte": 50}, 10),
        ({"sort_by": "popularity.desc", "primary_release_date.gte": "1990-01-01",
          "primary_release_date.lte": "1999-12-31", "vote_count.gte": 50}, 10),
        ({"sort_by": "popularity.desc", "primary_release_date.gte": "2000-01-01",
          "primary_release_date.lte": "2009-12-31", "vote_count.gte": 50}, 10),
        ({"sort_by": "popularity.desc", "primary_release_date.gte": "2010-01-01",
          "primary_release_date.lte": "2019-12-31", "vote_count.gte": 50}, 10),
        ({"sort_by": "popularity.desc", "primary_release_date.gte": "2020-01-01",
          "vote_count.gte": 30}, 10),

        # Tier 5 — All major genres (both popularity and rating sorts)
        ({"with_genres": "28",  "sort_by": "popularity.desc", "vote_count.gte": 100}, 10),   # Action
        ({"with_genres": "28",  "sort_by": "vote_average.desc", "vote_count.gte": 200}, 10),
        ({"with_genres": "35",  "sort_by": "popularity.desc", "vote_count.gte": 100}, 10),   # Comedy
        ({"with_genres": "35",  "sort_by": "vote_average.desc", "vote_count.gte": 200}, 10),
        ({"with_genres": "18",  "sort_by": "popularity.desc", "vote_count.gte": 100}, 10),   # Drama
        ({"with_genres": "18",  "sort_by": "vote_average.desc", "vote_count.gte": 200}, 10),
        ({"with_genres": "27",  "sort_by": "popularity.desc", "vote_count.gte": 100}, 10),   # Horror
        ({"with_genres": "27",  "sort_by": "vote_average.desc", "vote_count.gte": 200}, 10),
        ({"with_genres": "878", "sort_by": "popularity.desc", "vote_count.gte": 100}, 10),   # Sci-Fi
        ({"with_genres": "878", "sort_by": "vote_average.desc", "vote_count.gte": 200}, 10),
        ({"with_genres": "53",  "sort_by": "popularity.desc", "vote_count.gte": 100}, 10),   # Thriller
        ({"with_genres": "53",  "sort_by": "vote_average.desc", "vote_count.gte": 200}, 10),
        ({"with_genres": "10749", "sort_by": "popularity.desc", "vote_count.gte": 100}, 10), # Romance
        ({"with_genres": "10749", "sort_by": "vote_average.desc", "vote_count.gte": 200}, 10),
        ({"with_genres": "99",  "sort_by": "popularity.desc", "vote_count.gte": 100}, 10),   # Documentary
        ({"with_genres": "99",  "sort_by": "vote_average.desc", "vote_count.gte": 100}, 10),
        ({"with_genres": "16",  "sort_by": "popularity.desc", "vote_count.gte": 100}, 10),   # Animation
        ({"with_genres": "16",  "sort_by": "vote_average.desc", "vote_count.gte": 200}, 10),
        ({"with_genres": "80",  "sort_by": "popularity.desc", "vote_count.gte": 100}, 10),   # Crime
        ({"with_genres": "80",  "sort_by": "vote_average.desc", "vote_count.gte": 200}, 10),
        ({"with_genres": "9648", "sort_by": "popularity.desc", "vote_count.gte": 100}, 10),  # Mystery
        ({"with_genres": "9648", "sort_by": "vote_average.desc", "vote_count.gte": 200}, 10),
        ({"with_genres": "10752", "sort_by": "popularity.desc", "vote_count.gte": 100}, 10), # War
        ({"with_genres": "36",  "sort_by": "popularity.desc", "vote_count.gte": 100}, 10),   # History
        ({"with_genres": "10402", "sort_by": "popularity.desc", "vote_count.gte": 100}, 10), # Music
        ({"with_genres": "14",  "sort_by": "popularity.desc", "vote_count.gte": 100}, 10),   # Fantasy
        ({"with_genres": "12",  "sort_by": "popularity.desc", "vote_count.gte": 100}, 10),   # Adventure
        ({"with_genres": "10770", "sort_by": "popularity.desc", "vote_count.gte": 50}, 10),  # TV Movie

        # Tier 6 — Foreign languages (expanded)
        ({"with_original_language": "ko", "sort_by": "popularity.desc", "vote_count.gte": 50}, 10),   # Korean
        ({"with_original_language": "ko", "sort_by": "vote_average.desc", "vote_count.gte": 100}, 10),
        ({"with_original_language": "ja", "sort_by": "popularity.desc", "vote_count.gte": 50}, 10),   # Japanese
        ({"with_original_language": "ja", "sort_by": "vote_average.desc", "vote_count.gte": 100}, 10),
        ({"with_original_language": "fr", "sort_by": "popularity.desc", "vote_count.gte": 50}, 10),   # French
        ({"with_original_language": "fr", "sort_by": "vote_average.desc", "vote_count.gte": 100}, 10),
        ({"with_original_language": "es", "sort_by": "popularity.desc", "vote_count.gte": 50}, 10),   # Spanish
        ({"with_original_language": "es", "sort_by": "vote_average.desc", "vote_count.gte": 100}, 10),
        ({"with_original_language": "hi", "sort_by": "popularity.desc", "vote_count.gte": 50}, 10),   # Hindi
        ({"with_original_language": "hi", "sort_by": "vote_average.desc", "vote_count.gte": 100}, 10),
        ({"with_original_language": "it", "sort_by": "popularity.desc", "vote_count.gte": 50}, 10),   # Italian
        ({"with_original_language": "it", "sort_by": "vote_average.desc", "vote_count.gte": 100}, 10),
        ({"with_original_language": "zh", "sort_by": "popularity.desc", "vote_count.gte": 50}, 10),   # Chinese
        ({"with_original_language": "zh", "sort_by": "vote_average.desc", "vote_count.gte": 100}, 10),
        ({"with_original_language": "de", "sort_by": "popularity.desc", "vote_count.gte": 50}, 10),   # German
        ({"with_original_language": "pt", "sort_by": "popularity.desc", "vote_count.gte": 50}, 10),   # Portuguese
        ({"with_original_language": "ru", "sort_by": "popularity.desc", "vote_count.gte": 50}, 10),   # Russian
        ({"with_original_language": "tr", "sort_by": "popularity.desc", "vote_count.gte": 50}, 10),   # Turkish
    ]

    for params, pages in strategies:
        ids = discover_movies(params, max_pages = pages)
        before = len(all_ids)
        all_ids.update(ids)
        print(f"Fetched {len(ids)} IDs → {len(all_ids) - before} new (total: {len(all_ids)})")

    print(f"\nTotal unique IDs: {len(all_ids)}")
    print("Fetching full details...\n")

    movies = []
    id_list = list(all_ids)[:8000]
    output_path = "data/movies.json"

    # Resume support
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            movies = json.load(f)
        seen_ids = {m["id"] for m in movies}
        id_list = [i for i in id_list if i not in seen_ids]
        print(f"  ↩ Resuming — {len(movies)} saved, {len(id_list)} remaining\n")

    for i, movie_id in enumerate(id_list):
        movie = fetch_movie_details(movie_id)
        if movie and is_quality_movie(movie):
            movies.append(movie)

        if (i + 1) % 100 == 0:
            with open(output_path, "w", encoding = "utf-8") as f:
                json.dump(movies, f, ensure_ascii = False, indent = 2)
            print(f"Saved {len(movies)} movies ({i+1}/{len(id_list)} processed)")

        if len(movies) >= 5000:
            print("\nReached 5,000 movies — stopping")
            break

    with open(output_path, "w", encoding = "utf-8") as f:
        json.dump(movies, f, ensure_ascii = False, indent = 2)

    print(f"\nDone — {len(movies)} movies saved to data/movies.json")


if __name__ == "__main__":
    main()
