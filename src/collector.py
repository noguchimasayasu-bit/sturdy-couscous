import logging
import re
import urllib.parse
import xml.etree.ElementTree as ET
import yaml
import requests
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
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


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _parse_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str.strip())
    except Exception:
        return None


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en;q=0.9",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


def _encode_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    encoded_query = urllib.parse.quote(parsed.query, safe="=&")
    return urllib.parse.urlunsplit(parsed._replace(query=encoded_query))


def _fetch_feed(url: str) -> Optional[ET.Element]:
    resp = requests.get(_encode_url(url), headers=_HEADERS, timeout=15)
    resp.raise_for_status()
    return ET.fromstring(resp.content)


def _matches_keywords(text: str, keywords: List[str]) -> bool:
    if not keywords:
        return True
    return any(kw in text for kw in keywords)


def collect_news(config: dict) -> List[Article]:
    articles = []
    seen_urls: set = set()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    email_cfg = config.get("email", {})
    max_per_feed = email_cfg.get("max_articles_per_feed", 8)
    max_total = email_cfg.get("max_total_articles", 40)
    keywords: List[str] = email_cfg.get("keywords", [])

    for feed_cfg in config.get("rss_feeds", []):
        feed_name = feed_cfg["name"]
        url = feed_cfg["url"]

        try:
            logger.info(f"Fetching: {feed_name}")
            root = _fetch_feed(url)

            channel = root.find("channel")
            if channel is None:
                channel = root

            feed_title = feed_name
            title_el = channel.find("title")
            if title_el is not None and title_el.text:
                feed_title = title_el.text.strip()

            count = 0
            for item in channel.findall("item"):
                if count >= max_per_feed:
                    break

                link_el = item.find("link")
                article_url = (link_el.text or "").strip() if link_el is not None else ""
                if not article_url or article_url in seen_urls:
                    continue

                pub_el = item.find("pubDate")
                published = _parse_date(pub_el.text if pub_el is not None else None)
                if published and published.tzinfo is None:
                    published = published.replace(tzinfo=timezone.utc)
                if published and published < cutoff:
                    continue

                title_el = item.find("title")
                title = _strip_html(title_el.text if title_el is not None else "")

                desc_el = item.find("description")
                summary = _strip_html(desc_el.text if desc_el is not None else "")[:300]

                if not _matches_keywords(title + summary, keywords):
                    continue

                articles.append(Article(
                    title=title,
                    url=article_url,
                    summary=summary,
                    published=published,
                    source=feed_title,
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
