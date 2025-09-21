import feedparser
import json
import logging
import ssl
import time
import os
import requests
from urllib.parse import urlparse
from datetime import datetime, timezone
from collections import defaultdict

from app.settings import NEWS_SOURCES, REDDIT_SOURCES, PODCAST_SOURCES, KEYWORDS, BASE_DIR
from app.categorizer import Categorizer

try:
    os.umask(0o077)
except AttributeError:
    pass

log_file_path = BASE_DIR / "fetcher.log"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler(log_file_path, encoding='utf-8'), logging.StreamHandler()])
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0"

def get_current_utc_iso_string():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except:
        return False

def sanitize_entry(entry_data):
    title = entry_data.get("title", "No Title")
    link = entry_data.get("link", "")
    summary = entry_data.get("summary", "")

    if not isinstance(title, str) or not is_valid_url(link):
        return None
    
    entry_data["title"] = title[:300]
    entry_data["summary"] = summary[:2000]
    
    return entry_data

def fetch_feed_with_retry(source_name, url, max_retries=3, timeout=20):
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'application/rss+xml, application/xml, application/json'
    }
    
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempt {attempt + 1}/{max_retries} for source: {source_name}")
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()

            feed = feedparser.parse(response.text)
            
            if feed.bozo:
                raise Exception(f"Feed malformed after successful fetch. Bozo reason: {feed.bozo_exception}")

            break 
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** (attempt + 1)
                logging.warning(f"Network error on attempt {attempt + 1} for '{source_name}': {e}. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise Exception(f"Failed to fetch '{source_name}' after {max_retries} network attempts: {e}")
        except Exception as e:
            raise Exception(f"A non-network error occurred for '{source_name}': {e}")
    
    logging.info(f"  -> Found {len(feed.entries)} entries for {source_name}.")
    if not feed.entries:
        logging.warning(f"  -> No entries found for source: {source_name}")
    return feed

def fetch_news(categorizer: Categorizer):
    categorized_news = defaultdict(list)
    brazil_news = []
    
    all_sources = NEWS_SOURCES + REDDIT_SOURCES
    for source in all_sources:
        try:
            feed = fetch_feed_with_retry(source['name'], source['url'])
            
            is_brazilian_source = source.get("language") == "pt-br"
            
            for entry in feed.entries:
                news_item_raw = {
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.get("summary", ""),
                    "published": entry.get("published", entry.get("updated")),
                    "source_name": source['name'],
                    "timestamp_added": get_current_utc_iso_string(),
                    "color": source.get("color", "#6c757d"),
                    "type": source.get("type", "news"),
                    "category": source.get("category")
                }
                
                news_item = sanitize_entry(news_item_raw)
                if not news_item:
                    logging.warning(f"  -> Discarding invalid entry: {news_item_raw.get('title')}")
                    continue

                if is_brazilian_source:
                    brazil_news.append(news_item)
                else:
                    category = categorizer.categorize(news_item["title"], news_item["summary"])
                    categorized_news[category].append(news_item)
        except Exception as e:
            logging.error(f"SKIPPING source '{source['name']}' due to persistent failure. Reason: {e}")
            continue
    
    if brazil_news:
        categorized_news["Brazil"] = brazil_news
    return dict(categorized_news)

def fetch_podcasts():
    show_episodes = defaultdict(list)
    if not PODCAST_SOURCES:
        logging.warning("Podcast list is empty in sources.json. Skipping podcast fetch.")
        return {}

    for podcast in PODCAST_SOURCES:
        try:
            feed = fetch_feed_with_retry(podcast['name'], podcast['url'])
            
            for entry in feed.entries:
                audio_url = ""
                if hasattr(entry, 'enclosures'):
                    for enc in entry.enclosures:
                        if 'audio' in enc.type:
                            audio_url = enc.href
                            break
                
                episode_item_raw = {
                    "title": entry.title,
                    "link": entry.link,
                    "audio_url": audio_url,
                    "summary": entry.get("summary", ""),
                    "published": entry.get("published", entry.get("updated")),
                    "show_name": podcast['name'],
                    "timestamp_added": get_current_utc_iso_string()
                }

                episode_item = sanitize_entry(episode_item_raw)
                if not episode_item:
                    logging.warning(f"  -> Discarding invalid episode: {episode_item_raw.get('title')}")
                    continue

                show_episodes[podcast['name']].append(episode_item)
        except Exception as e:
            logging.error(f"SKIPPING podcast '{podcast['name']}' due to persistent failure. Reason: {e}")
            continue

    return dict(show_episodes)

if __name__ == "__main__":
    logging.info("--- Starting new content fetch cycle ---")
    news_categorizer = Categorizer(KEYWORDS)
    final_data = {"news": fetch_news(news_categorizer), "podcasts": fetch_podcasts()}
    output_path = BASE_DIR / "public" / "data.json"
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        logging.info(f"Successfully generated data file at: {output_path}")
    except IOError as e:
        logging.critical(f"Fatal: Could not write to data file {output_path}: {e}")
    logging.info("--- Content fetch cycle finished ---")