import logging
import os

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To

logger = logging.getLogger(__name__)


def send_email(subject: str, html_body: str, recipient: str) -> bool:
    api_key = os.environ.get("SENDGRID_API_KEY", "")
    sender_email = os.environ.get("SENDER_EMAIL", "")

    if not api_key:
        logger.error("SENDGRID_API_KEY が設定されていません")
        return False
    if not sender_email:
        logger.error("SENDER_EMAIL が設定されていません")
        return False

    message = Mail(
        from_email=sender_email,
        to_emails=To(recipient),
        subject=subject,
        html_content=html_body,
    )

    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        logger.info(f"メール送信完了 (status={response.status_code}) → {recipient}")
        return True
    except Exception as e:
        logger.error(f"SendGrid送信エラー: {e}")
        return False
