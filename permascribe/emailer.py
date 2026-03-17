import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send_summary(config: dict, date_str: str, summary: str):
    ec = config["email"]
    if not ec["enabled"]:
        return

    if not ec["smtp_user"] or not ec["smtp_password"] or not ec["to"]:
        logger.warning("Email enabled but SMTP credentials not configured")
        return

    subject = f"{ec['subject_prefix']} Daily Summary — {date_str}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = ec["smtp_user"]
    msg["To"] = ec["to"]

    # Plain text version
    msg.attach(MIMEText(summary, "plain", "utf-8"))

    # HTML version (wrap markdown in <pre> for simplicity)
    html = f"""<html><body>
<h2>PermaScribe Daily Summary — {date_str}</h2>
<pre style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            white-space: pre-wrap; line-height: 1.6; font-size: 14px;">
{summary}
</pre>
</body></html>"""
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(ec["smtp_host"], ec["smtp_port"]) as server:
            server.starttls()
            server.login(ec["smtp_user"], ec["smtp_password"])
            server.sendmail(ec["smtp_user"], ec["to"], msg.as_string())
        logger.info(f"Summary email sent to {ec['to']}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
