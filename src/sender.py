import logging
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

logger = logging.getLogger(__name__)


def send_email(subject: str, html_body: str, recipient: str) -> bool:
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    sender_email = os.environ.get("SENDER_EMAIL", smtp_user)

    if not smtp_user or not smtp_password:
        logger.error("SMTP_USER と SMTP_PASSWORD を設定してください")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"ニュースダイジェスト <{sender_email}>"
    msg["To"] = recipient
    msg["Date"] = formatdate(localtime=True)

    plain_text = f"{subject}\n\nこのメールはHTML形式です。HTMLメールに対応したメールクライアントでご覧ください。"
    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(smtp_user, smtp_password)
            server.sendmail(sender_email, [recipient], msg.as_string())
        logger.info(f"メール送信完了 → {recipient}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail認証エラー。SMTP_USER と SMTP_PASSWORD を確認してください。")
        return False
    except Exception as e:
        logger.error(f"送信エラー: {e}")
        return False
