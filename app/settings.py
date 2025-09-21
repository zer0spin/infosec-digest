import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def load_sources():
    """Loads the main sources.json file."""
    try:
        with open(BASE_DIR / 'sources.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            return (
                config.get("news_sources", []),
                config.get("reddit_sources", []),
                config.get("podcast_sources", [])
            )
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading sources.json: {e}")
        return [], [], []

def load_keywords():
    """Loads the keywords.json file."""
    try:
        with open(BASE_DIR / 'keywords.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading keywords.json: {e}")
        return {}

# Load all configurations
NEWS_SOURCES, REDDIT_SOURCES, PODCAST_SOURCES = load_sources()
KEYWORDS = load_keywords()