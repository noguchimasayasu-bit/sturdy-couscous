#!/usr/bin/env python3
"""
機械・造船・プラントセクター ニュース自動収集・メール配信

使用方法:
  python main.py

環境変数（.envファイルまたはGitHub Secrets）:
  RECIPIENT_EMAIL  - 配信先メールアドレス（必須）
  SMTP_USER        - 送信元メールアドレス（必須）
  SMTP_PASSWORD    - SMTPパスワードまたはアプリパスワード（必須）
  SMTP_HOST        - SMTPサーバー（省略時: smtp.gmail.com）
  SMTP_PORT        - SMTPポート（省略時: 587）
  SENDER_EMAIL     - 差出人メールアドレス（省略時: SMTP_USERと同じ）
"""
import logging
import os
import sys

from dotenv import load_dotenv

from src.collector import collect_news, load_config
from src.formatter import format_email
from src.sender import send_email

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    recipient = os.environ.get("RECIPIENT_EMAIL")
    if not recipient:
        logger.error("環境変数 RECIPIENT_EMAIL が設定されていません")
        sys.exit(1)

    config_path = os.environ.get("CONFIG_PATH", "config.yaml")
    config = load_config(config_path)

    logger.info("ニュース収集を開始します...")
    articles = collect_news(config)
    logger.info(f"{len(articles)} 件の記事を収集しました")

    if not articles:
        logger.warning("記事が見つかりませんでした。メール配信をスキップします。")
        return

    subject, html_body = format_email(articles, config)
    logger.info(f"件名: {subject}")

    success = send_email(subject, html_body, recipient)
    if not success:
        logger.error("メール配信に失敗しました")
        sys.exit(1)

    logger.info("メール配信が完了しました")


if __name__ == "__main__":
    main()
