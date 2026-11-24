"""Gmail functions: search, read and create drafts. Nothing sends or deletes."""

import base64
import html
import re
from email.message import EmailMessage

from google_auth import gmail_service

MAX_RESULTS = 50
MAX_BODY_CHARS = 20_000


def _headers(payload: dict) -> dict:
    return {h["name"].lower(): h["value"] for h in payload.get("headers", [])}


def _summary(message: dict) -> dict:
    headers = _headers(message.get("payload", {}))
    return {
        "id": message["id"],
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "subject": headers.get("subject", ""),
        "date": headers.get("date", ""),
        "snippet": html.unescape(message.get("snippet", "")),
    }


def _find_text(part: dict, mime_type: str) -> str:
    """Return the first non-attachment text of this type in the message."""
    data = part.get("body", {}).get("data")
    if part.get("mimeType") == mime_type and data and not part.get("filename"):
        raw = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
        content_type = _headers(part).get("content-type", "")
        match = re.search(r'charset="?([\w.:-]+)', content_type, re.I)
        try:
            return raw.decode(match.group(1) if match else "utf-8", "replace")
        except LookupError:
            return raw.decode("utf-8", "replace")
    for child in part.get("parts", []):
        text = _find_text(child, mime_type)
        if text:
            return text
    return ""


def _html_to_text(source: str) -> str:
    source = re.sub(r"(?is)<(script|style)\b.*?</\1>", "", source)
    source = re.sub(r"(?i)<br\s*/?>|</(p|div|tr|li|h\d)>", "\n", source)
    text = html.unescape(re.sub(r"<[^>]+>", "", source))
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def search_emails(query: str, max_results: int) -> list[dict]:
    if not 1 <= max_results <= MAX_RESULTS:
        raise ValueError(f"max_results must be between 1 and {MAX_RESULTS}.")
    messages = gmail_service().users().messages()
    found = messages.list(userId="me", q=query, maxResults=max_results).execute()
    return [
        _summary(
            messages.get(
                userId="me",
                id=item["id"],
                format="metadata",
                metadataHeaders=["From", "To", "Subject", "Date"],
            ).execute()
        )
        for item in found.get("messages", [])
    ]


def read_email(message_id: str) -> dict:
    messages = gmail_service().users().messages()
    message = messages.get(userId="me", id=message_id, format="full").execute()
    payload = message.get("payload", {})
    body = _find_text(payload, "text/plain")
    if not body:
        body = _html_to_text(_find_text(payload, "text/html"))
    return {
        **_summary(message),
        "body": body[:MAX_BODY_CHARS],
        "truncated": len(body) > MAX_BODY_CHARS,
    }


def create_draft(to: str, subject: str, body: str) -> dict:
    email = EmailMessage()
    email["To"] = to
    email["Subject"] = subject
    email.set_content(body)
    raw = base64.urlsafe_b64encode(email.as_bytes()).decode()
    drafts = gmail_service().users().drafts()
    draft = drafts.create(userId="me", body={"message": {"raw": raw}}).execute()
    return {"draft_id": draft["id"], "status": "Draft saved. It was NOT sent."}
