"""Primary-calendar functions. Nothing deletes events or sends invitations."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from google_auth import calendar_service

TIME_ZONE = "Asia/Jerusalem"
TZ = ZoneInfo(TIME_ZONE)
DAY_START = time(8, 0)
DAY_END = time(20, 0)


def _local(text: str) -> datetime:
    """Parse ISO 8601 text. No UTC offset means Asia/Jerusalem."""
    value = datetime.fromisoformat(text)
    return value.replace(tzinfo=TZ) if value.tzinfo is None else value.astimezone(TZ)


def _fetch(start: datetime, end: datetime) -> list[dict]:
    events = calendar_service().events()
    items, page_token = [], None
    while True:
        page = events.list(
            calendarId="primary",
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            timeZone=TIME_ZONE,
            maxResults=250,
            pageToken=page_token,
        ).execute()
        items += page.get("items", [])
        page_token = page.get("nextPageToken")
        if not page_token:
            return items


def _summary(event: dict) -> dict:
    start, end = event["start"], event["end"]
    return {
        "id": event["id"],
        "title": event.get("summary", "(no title)"),
        "start": start.get("dateTime") or start.get("date"),
        "end": end.get("dateTime") or end.get("date"),
        "all_day": "date" in start,
        "location": event.get("location", ""),
        "description": event.get("description", ""),
    }


def _is_busy(event: dict) -> bool:
    """Ignore events marked Free and invitations the user declined."""
    declined = any(
        guest.get("self") and guest.get("responseStatus") == "declined"
        for guest in event.get("attendees", [])
    )
    return event.get("transparency") != "transparent" and not declined


def _utc(point: dict) -> datetime:
    return _local(point.get("dateTime") or point["date"]).astimezone(UTC)


def list_events(days_ahead: int) -> list[dict]:
    if not 1 <= days_ahead <= 365:
        raise ValueError("days_ahead must be between 1 and 365.")
    now = datetime.now(TZ)
    return [_summary(e) for e in _fetch(now, now + timedelta(days=days_ahead))]


def find_free_slots(day_text: str, duration_minutes: int) -> list[dict]:
    if not 1 <= duration_minutes <= 720:
        raise ValueError("duration_minutes must be between 1 and 720.")
    day = date.fromisoformat(day_text)
    # Calculate in UTC so daylight-saving changes cannot skew the result.
    start = datetime.combine(day, DAY_START, TZ).astimezone(UTC)
    end = datetime.combine(day, DAY_END, TZ).astimezone(UTC)
    now = datetime.now(UTC).replace(second=0, microsecond=0) + timedelta(minutes=1)
    start = max(start, now)
    if start >= end:
        return []
    busy = sorted(
        (_utc(e["start"]), _utc(e["end"])) for e in _fetch(start, end) if _is_busy(e)
    )
    slots, cursor = [], start
    for busy_start, busy_end in [*busy, (end, end)]:
        gap_end = min(busy_start, end)
        if gap_end - cursor >= timedelta(minutes=duration_minutes):
            slots.append(
                {
                    "start": cursor.astimezone(TZ).isoformat(),
                    "end": gap_end.astimezone(TZ).isoformat(),
                }
            )
        cursor = max(cursor, busy_end)
    return slots


def create_event(title: str, start: str, end: str, description: str) -> dict:
    start_at, end_at = _local(start), _local(end)
    if end_at.astimezone(UTC) <= start_at.astimezone(UTC):
        raise ValueError("end must be after start.")
    event = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start_at.isoformat(), "timeZone": TIME_ZONE},
        "end": {"dateTime": end_at.isoformat(), "timeZone": TIME_ZONE},
    }
    created = calendar_service().events().insert(
        calendarId="primary", body=event, sendUpdates="none"
    ).execute()
    return {**_summary(created), "link": created.get("htmlLink", "")}
