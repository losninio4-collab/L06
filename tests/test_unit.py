"""Offline unit tests: Google is always mocked and no real account is used."""

import asyncio
import base64
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import httplib2
import pytest
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError

import calendar_tools
import gmail_tools
import google_auth
import server

DAY = (datetime.now(calendar_tools.TZ) + timedelta(days=3)).date().isoformat()


def event(start, end, **extra):
    def point(clock):
        local = datetime.fromisoformat(f"{DAY}T{clock}").replace(tzinfo=calendar_tools.TZ)
        return {"dateTime": local.isoformat()}

    return {"id": "x", "start": point(start), "end": point(end), **extra}


def free(monkeypatch, events, minutes=60):
    monkeypatch.setattr(calendar_tools, "_fetch", lambda start, end: events)
    slots = calendar_tools.find_free_slots(DAY, minutes)
    return [(s["start"][11:16], s["end"][11:16]) for s in slots]


@pytest.fixture
def gmail(monkeypatch):
    service = MagicMock()
    monkeypatch.setattr(gmail_tools, "gmail_service", lambda: service)
    return service


@pytest.fixture
def calendar(monkeypatch):
    service = MagicMock()
    monkeypatch.setattr(calendar_tools, "calendar_service", lambda: service)
    return service


def test_exact_tool_list():
    tools = asyncio.run(server.mcp.list_tools())
    assert {tool.name for tool in tools} == {
        "search_emails", "read_email", "create_draft",
        "list_events", "find_free_slots", "create_event",
    }
    assert all(tool.description for tool in tools)


def test_search_emails(gmail):
    messages = gmail.users().messages()
    messages.list.return_value.execute.return_value = {"messages": [{"id": "1"}]}
    headers = [{"name": "Subject", "value": "Hi"}]
    messages.get.return_value.execute.return_value = {
        "id": "1", "payload": {"headers": headers},
    }
    assert gmail_tools.search_emails("is:unread", 5)[0]["subject"] == "Hi"
    messages.list.assert_called_with(userId="me", q="is:unread", maxResults=5)


def test_read_html_email(gmail):
    data = base64.urlsafe_b64encode("<p>hi</p>שלום".encode()).decode()
    gmail.users().messages().get.return_value.execute.return_value = {
        "id": "1", "payload": {"mimeType": "text/html", "body": {"data": data}},
    }
    assert gmail_tools.read_email("1")["body"] == "hi\nשלום"


def test_draft_is_created_and_never_sent(gmail):
    drafts = gmail.users().drafts()
    drafts.create.return_value.execute.return_value = {"id": "d1"}
    assert gmail_tools.create_draft("a@example.com", "שלום", "גוף")["draft_id"] == "d1"
    raw = drafts.create.call_args.kwargs["body"]["message"]["raw"]
    assert "גוף" in base64.urlsafe_b64decode(raw).decode()
    drafts.send.assert_not_called()
    gmail.users().messages().send.assert_not_called()


def test_draft_rejects_header_injection():
    with pytest.raises(ValueError):
        gmail_tools.create_draft("a@example.com\nBcc: b@example.com", "s", "b")


def test_list_events_reads_every_page(calendar):
    calendar.events().list.return_value.execute.side_effect = [
        {"items": [event("09:00", "10:00")], "nextPageToken": "p2"},
        {"items": [event("11:00", "12:00")]},
    ]
    assert len(calendar_tools.list_events(7)) == 2


def test_free_slots_merge_overlaps(monkeypatch):
    events = [event("09:00", "10:00"), event("09:30", "11:00"), event("19:30", "21:00")]
    assert free(monkeypatch, events) == [("08:00", "09:00"), ("11:00", "19:30")]


def test_free_slots_ignore_free_and_declined(monkeypatch):
    declined = [{"self": True, "responseStatus": "declined"}]
    events = [
        event("12:00", "13:00", transparency="transparent"),
        event("14:00", "15:00", attendees=declined),
    ]
    assert free(monkeypatch, events) == [("08:00", "20:00")]


def test_create_event_has_no_guests(calendar):
    calendar.events().insert.return_value.execute.return_value = event("09:00", "10:00")
    calendar_tools.create_event("t", f"{DAY}T09:00", f"{DAY}T10:00", "")
    call = calendar.events().insert.call_args.kwargs
    assert call["sendUpdates"] == "none" and "attendees" not in call["body"]
    assert call["body"]["start"]["timeZone"] == "Asia/Jerusalem"


def test_invalid_input_is_rejected():
    with pytest.raises(ValueError):
        calendar_tools.create_event("t", f"{DAY}T10:00", f"{DAY}T09:00", "")
    with pytest.raises(ValueError):
        calendar_tools.list_events(0)
    with pytest.raises(ValueError):
        gmail_tools.search_emails("x", 999)


def test_missing_setup_is_reported(monkeypatch, tmp_path):
    monkeypatch.delenv(google_auth.ENV_VAR, raising=False)
    with pytest.raises(google_auth.GoogleSetupError, match="not set"):
        google_auth.load_credentials()
    monkeypatch.setenv(google_auth.ENV_VAR, str(tmp_path))
    with pytest.raises(google_auth.GoogleSetupError, match="token.json"):
        google_auth.load_credentials()


@pytest.mark.parametrize("error", [
    RefreshError("SECRET"),
    HttpError(httplib2.Response({"status": 403}), b"SECRET"),
])
def test_google_errors_hide_details(error):
    with pytest.raises(RuntimeError) as caught:
        google_auth.safe_errors(MagicMock(side_effect=error, __name__="f"))()
    assert "SECRET" not in str(caught.value)
