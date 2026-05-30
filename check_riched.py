import json

with open('data/movies_enriched.json', 'r', encoding='utf-8') as f:
    movies = json.load(f)

print(f'Total enriched: {len(movies)}')
missing = [m['title'] for m in movies if not m.get('themes')]
print(f'Missing themes: {len(missing)}')