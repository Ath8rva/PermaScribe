import html
import logging
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def _parse_sections(summary: str) -> dict[str, str]:
    """Split markdown summary by ## headers into a dict."""
    sections = {}
    current_key = "_preamble"
    current_lines = []

    for line in summary.split("\n"):
        if line.startswith("## "):
            if current_lines:
                sections[current_key] = "\n".join(current_lines).strip()
            current_key = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections[current_key] = "\n".join(current_lines).strip()

    return sections


def _md_table_to_html(md_text: str) -> str:
    """Convert a markdown table to a styled HTML table."""
    lines = [l.strip() for l in md_text.strip().split("\n") if l.strip()]

    # Find table lines (contain |)
    table_lines = [l for l in lines if "|" in l]
    non_table = [l for l in lines if "|" not in l]

    if len(table_lines) < 2:
        # No real table, just return escaped text
        return f"<p style='color:#D1D5DB;line-height:1.7;'>{html.escape(md_text)}</p>"

    # Parse header
    header_cells = [c.strip() for c in table_lines[0].split("|") if c.strip()]

    # Skip separator line (---|---|...)
    data_start = 1
    if len(table_lines) > 1 and re.match(r'^[\s|:-]+$', table_lines[1]):
        data_start = 2

    # Parse rows
    rows = []
    for line in table_lines[data_start:]:
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if cells:
            rows.append(cells)

    # Build HTML table
    h = '<table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:14px;">'

    # Header row
    h += '<tr>'
    for cell in header_cells:
        h += f'<th style="padding:10px 14px;text-align:left;color:#1A6FE8;font-size:11px;font-weight:600;letter-spacing:1px;text-transform:uppercase;border-bottom:2px solid #1F2937;">{html.escape(cell)}</th>'
    h += '</tr>'

    # Data rows
    for i, row in enumerate(rows):
        bg = "#111827" if i % 2 == 0 else "#0F1117"
        h += f'<tr style="background-color:{bg};">'
        for j, cell in enumerate(row):
            h += f'<td style="padding:10px 14px;color:#D1D5DB;border-bottom:1px solid #1F2937;">{html.escape(cell)}</td>'
        # Pad if row has fewer cells than header
        for _ in range(len(header_cells) - len(row)):
            h += f'<td style="padding:10px 14px;color:#D1D5DB;border-bottom:1px solid #1F2937;">—</td>'
        h += '</tr>'

    h += '</table>'

    # Prepend any non-table text
    if non_table:
        prefix = "".join(f"<p style='color:#D1D5DB;line-height:1.7;margin:0 0 8px 0;'>{html.escape(l)}</p>" for l in non_table)
        return prefix + h

    return h


def _bullets_to_html(text: str, color: str = "#E0E0E0") -> str:
    """Convert markdown bullet/numbered list to HTML list items."""
    items = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Strip leading bullets, dashes, numbers
        line = re.sub(r'^[-*]\s*', '', line)
        line = re.sub(r'^\d+[\.\)]\s*', '', line)
        if line:
            items.append(f"<li style='margin-bottom:8px;color:{color};line-height:1.6;'>{html.escape(line)}</li>")
    return "\n".join(items)


def _text_to_paragraphs(text: str, color: str = "#D1D5DB") -> str:
    """Convert plain text to HTML paragraphs."""
    paras = []
    for line in text.split("\n"):
        line = line.strip()
        if line:
            paras.append(f"<p style='margin:0 0 8px 0;color:{color};line-height:1.7;font-size:15px;'>{html.escape(line)}</p>")
    return "\n".join(paras)


def _build_card(label: str, content_html: str, accent: str = "#1A6FE8") -> str:
    """Build a styled card section."""
    return f"""<tr><td style="padding:0 0 28px 0;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#111827;border-radius:8px;border-left:3px solid {accent};">
    <tr><td style="padding:20px 24px;">
      <p style="margin:0 0 12px 0;font-size:11px;font-weight:600;letter-spacing:1.5px;color:{accent};text-transform:uppercase;">{html.escape(label)}</p>
      {content_html}
    </td></tr>
  </table>
</td></tr>"""


def _build_dark_box(label: str, content_html: str) -> str:
    """Build a dark box section with label above."""
    return f"""<tr><td style="padding:0 0 28px 0;">
  <p style="margin:0 0 14px 0;font-size:11px;font-weight:600;letter-spacing:1.5px;color:#6B7280;text-transform:uppercase;">{html.escape(label)}</p>
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0F1117;border-radius:8px;">
    <tr><td style="padding:20px 24px;">
      {content_html}
    </td></tr>
  </table>
</td></tr>"""


def build_html_email(date_str: str, summary: str) -> str:
    """Build a professional dark-theme HTML email from the markdown summary."""
    safe = html.escape
    sections = _parse_sections(summary)

    # Day Overview
    overview = sections.get("Day Overview", "")
    overview_html = _build_card(
        "Day Overview",
        _text_to_paragraphs(overview),
        "#1A6FE8",
    ) if overview else ""

    # Work Tracker
    work_tracker = sections.get("Work Tracker", "")
    work_tracker_html = ""
    if work_tracker and "no tracked work" not in work_tracker.lower():
        work_tracker_html = _build_dark_box(
            "Work Tracker",
            _md_table_to_html(work_tracker),
        )

    # Action Items
    action_items = sections.get("Action Items / To-Dos", "")
    action_html = ""
    if action_items and action_items.strip():
        items_li = _bullets_to_html(action_items)
        if items_li:
            action_html = _build_card(
                "Action Items",
                f'<ul style="margin:0;padding-left:18px;font-size:14px;list-style-type:disc;">{items_li}</ul>',
                "#22C55E",
            )

    # Key Conversations
    conversations = sections.get("Key Conversations & Topics", "")
    conversations_html = ""
    if conversations:
        conv_li = _bullets_to_html(conversations)
        if conv_li:
            conversations_html = _build_dark_box(
                "Key Conversations & Topics",
                f'<ul style="margin:0;padding-left:18px;font-size:14px;list-style-type:disc;">{conv_li}</ul>',
            )

    # Key Decisions
    decisions = sections.get("Key Decisions", "")
    decisions_html = ""
    if decisions and decisions.strip():
        dec_li = _bullets_to_html(decisions)
        if dec_li:
            decisions_html = _build_card(
                "Key Decisions",
                f'<ul style="margin:0;padding-left:18px;font-size:14px;list-style-type:disc;">{dec_li}</ul>',
                "#F59E0B",
            )

    # Notable Quotes
    quotes = sections.get("Notable Quotes", "")
    quotes_html = ""
    if quotes and quotes.strip():
        quotes_html = _build_dark_box(
            "Notable Quotes",
            _text_to_paragraphs(quotes, "#B0B0B0"),
        )

    # Mood & Energy
    mood = sections.get("Mood & Energy", "")
    mood_html = ""
    if mood and mood.strip():
        mood_html = f"""<tr><td style="padding:0 0 28px 0;">
  <p style="margin:0;font-size:13px;color:#6B7280;font-style:italic;line-height:1.6;">{safe(mood)}</p>
</td></tr>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#0A0A0A;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0A0A0A;padding:32px 16px;">
    <tr><td align="center">
      <table width="100%" style="max-width:640px;background-color:#0A0A0A;">

        <!-- Header -->
        <tr><td style="padding:0 0 24px 0;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td style="padding:20px 0;border-bottom:2px solid #1A6FE8;">
                <span style="font-size:13px;font-weight:600;letter-spacing:2px;color:#1A6FE8;text-transform:uppercase;">PermaScribe</span>
              </td>
            </tr>
          </table>
        </td></tr>

        <!-- Date -->
        <tr><td style="padding:0 0 32px 0;">
          <h1 style="margin:0;font-size:22px;font-weight:700;color:#FFFFFF;line-height:1.3;">Daily Summary — {safe(date_str)}</h1>
        </td></tr>

        {overview_html}
        {work_tracker_html}
        {action_html}
        {conversations_html}
        {decisions_html}
        {quotes_html}
        {mood_html}

        <!-- Footer -->
        <tr><td style="padding:24px 0 0 0;border-top:1px solid #1F2937;">
          <p style="margin:0;font-size:11px;color:#4B5563;text-align:center;">
            Generated by PermaScribe &middot; Always-on audio transcription &amp; AI summarization
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


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

    # HTML version
    html_body = build_html_email(date_str, summary)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(ec["smtp_host"], ec["smtp_port"]) as server:
            server.starttls()
            server.login(ec["smtp_user"], ec["smtp_password"])
            server.sendmail(ec["smtp_user"], ec["to"], msg.as_string())
        logger.info(f"Summary email sent to {ec['to']}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
