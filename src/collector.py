import re
import logging
import feedparser
import yaml
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))


@dataclass
class Article:
    title: str
    url: str
    summary: str
    published: Optional[datetime]
    source: str
    feed_name: str


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _parse_published(entry) -> Optional[datetime]:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    return None


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def collect_news(config: dict) -> List[Article]:
    articles = []
    seen_urls = set()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    max_per_feed = config.get("email", {}).get("max_articles_per_feed", 5)
    max_total = config.get("email", {}).get("max_total_articles", 40)

    for feed_cfg in config.get("rss_feeds", []):
        feed_name = feed_cfg["name"]
        url = feed_cfg["url"]

        try:
            logger.info(f"Fetching: {feed_name}")
            feed = feedparser.parse(url)

            count = 0
            for entry in feed.entries:
                if count >= max_per_feed:
                    break

                article_url = entry.get("link", "")
                if article_url in seen_urls:
                    continue

                published = _parse_published(entry)
                if published and published < cutoff:
                    continue

                summary = ""
                if hasattr(entry, "summary"):
                    summary = _strip_html(entry.summary)[:300]

                articles.append(Article(
                    title=entry.get("title", "").strip(),
                    url=article_url,
                    summary=summary,
                    published=published,
                    source=feed.feed.get("title", feed_name),
                    feed_name=feed_name,
                ))
                seen_urls.add(article_url)
                count += 1

        except Exception as e:
            logger.error(f"Error fetching {feed_name}: {e}")

    articles.sort(
        key=lambda a: a.published or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return articles[:max_total]
