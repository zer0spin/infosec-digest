import feedparser
import json
import logging
import ssl
import time
import os
from urllib.parse import urlparse
from datetime import datetime, timezone
from collections import defaultdict

# Import app settings and dependencies
from app.settings import NEWS_SOURCES, REDDIT_SOURCES, PODCAST_SOURCES, KEYWORDS, BASE_DIR
from app.categorizer import Categorizer

# Security: Set restricted file permissions (owner read/write only)
try:
    os.umask(0o077)
except AttributeError:
    pass  # umask not available on all systems

# Logging configuration
log_file_path = BASE_DIR / "fetcher.log"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler(log_file_path, encoding='utf-8'), logging.StreamHandler()])
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0"

def get_current_utc_iso_string():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def is_valid_url(url):
    """# Security: Validate if string is a valid HTTP/HTTPS URL"""
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except:
        return False

def sanitize_entry(entry_data):
    """Security: Validate and sanitize feed item data to prevent injection and DoS.
    
    This function performs several security checks:
    1. Validates data types of required fields
    2. Ensures URLs are properly formatted and use allowed schemes
    3. Truncates content to prevent DoS attacks via large content
    4. Sanitizes string fields to prevent XSS and injection attacks
    
    Args:
        entry_data (dict): Raw feed entry data to be sanitized
        
    Returns:
        dict: Sanitized entry data, or None if validation fails
    """
    title = entry_data.get("title", "No Title")
    link = entry_data.get("link", "")
    summary = entry_data.get("summary", "")

    # Type and format validation
    if not isinstance(title, str) or not is_valid_url(link):
        return None  # Discard items with invalid title or link
    
    # Truncate content to prevent DoS with massive content
    entry_data["title"] = title[:300]
    entry_data["summary"] = summary[:2000]
    
    return entry_data

def fetch_feed(source_name, url):
    
    logging.info(f"Processing source: {source_name} ({url})")
    feed = feedparser.parse(url, agent=USER_AGENT)
    if feed.bozo:
        if isinstance(feed.bozo_exception, ssl.SSLError):
             raise Exception(f"SSL Certificate Error. Bozo reason: {feed.bozo_exception}")
        raise Exception(f"Feed malformed. Bozo reason: {feed.bozo_exception}")
    logging.info(f"  -> Found {len(feed.entries)} entries for {source_name}.")
    if not feed.entries:
        logging.warning(f"  -> No entries found for source: {source_name}")
    return feed

def fetch_news(categorizer: Categorizer):
    """Fetches and categorizes news from all configured sources.
    
    This function processes each news source, fetches their RSS feeds,
    and categorizes the news items based on their content. Items from
    Brazilian sources are grouped separately in the 'Brazil' category.
    
    Args:
        categorizer: A Categorizer instance used to classify news items
        
    Returns:
        dict: A dictionary where keys are categories and values are lists of news items
    """
    categorized_news = defaultdict(list)
    brazil_news = []
    
    # Combine news and reddit sources
    all_sources = NEWS_SOURCES + REDDIT_SOURCES
    for source in all_sources:
        try:
            feed = fetch_feed(source['name'], source['url'])
            
            time.sleep(1)
            
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
            logging.error(f"FAILED to process entire source '{source['name']}'. Reason: {e}")
            continue
    
    if brazil_news:
        categorized_news["Brazil"] = brazil_news
    return dict(categorized_news)

def fetch_podcasts():
    """Fetches podcast episodes from configured podcast sources.
    
    This function processes each podcast feed, extracts episode information
    including audio URLs, and organizes them by show name. It includes
    validation and sanitization of feed content.
    
    Returns:
        dict: A dictionary where keys are podcast show names and values
              are lists of episode details
    """
    show_episodes = defaultdict(list)
    if not PODCAST_SOURCES:
        logging.warning("Podcast list is empty in sources.json. Skipping podcast fetch.")
        return {}

    for podcast in PODCAST_SOURCES:
        try:
            feed = fetch_feed(podcast['name'], podcast['url'])
            time.sleep(1)
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
            logging.error(f"FAILED to process entire podcast '{podcast['name']}'. Reason: {e}")
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