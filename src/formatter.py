import os
from datetime import datetime, timedelta, timezone
from typing import List

from jinja2 import Environment, FileSystemLoader

from .collector import Article

JST = timezone(timedelta(hours=9))


def format_email(articles: List[Article], config: dict) -> tuple:
    """Returns (subject, html_body)."""
    now_jst = datetime.now(JST)
    date_str = now_jst.strftime("%Y年%m月%d日")

    subject_prefix = config.get("email", {}).get(
        "subject_prefix", "【機械・造船・プラントセクター】ニュースダイジェスト"
    )
    subject = f"{subject_prefix} {date_str}"

    grouped: dict[str, List[Article]] = {}
    for article in articles:
        grouped.setdefault(article.feed_name, []).append(article)

    template_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "templates"
    )
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
    template = env.get_template("email_template.html")

    html_body = template.render(
        date=date_str,
        articles=articles,
        grouped_articles=grouped,
        total_count=len(articles),
        companies=config.get("companies", []),
        generated_at=now_jst.strftime("%Y-%m-%d %H:%M JST"),
    )

    return subject, html_body
