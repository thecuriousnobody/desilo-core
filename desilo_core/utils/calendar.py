"""
Calendar Utilities

Generate iCalendar (.ics) files for event invites. Works with any
email delivery provider — just attach the .ics content as a file.

Supports:
  - Single event .ics generation
  - Standard iCalendar (RFC 5545) format
  - Timezone-aware datetimes
"""

import re
import uuid
import logging
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CalendarEvent:
    """A calendar event to be converted to .ics format."""
    title: str
    start: datetime
    description: str = ""
    location: str = ""
    url: str = ""
    duration_hours: float = 1.0
    organizer_name: str = ""
    organizer_email: str = ""
    uid: str = field(default_factory=lambda: f"{uuid.uuid4()}@desilo")


def _escape_ics_text(text: str) -> str:
    """Escape special characters for iCalendar text fields."""
    text = text.replace("\\", "\\\\")
    text = text.replace(";", "\\;")
    text = text.replace(",", "\\,")
    text = text.replace("\n", "\\n")
    return text


def _format_ics_datetime(dt: datetime) -> str:
    """Format a datetime for iCalendar (UTC)."""
    return dt.strftime("%Y%m%dT%H%M%SZ")


def generate_ics(event: CalendarEvent) -> str:
    """Generate an iCalendar (.ics) string for a single event.

    Args:
        event: A CalendarEvent with at minimum a title and start time.

    Returns:
        A string containing valid iCalendar data (RFC 5545).
    """
    end = event.start + timedelta(hours=event.duration_hours)
    now = datetime.now(timezone.utc)

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//DeSilo//Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{event.uid}",
        f"DTSTART:{_format_ics_datetime(event.start)}",
        f"DTEND:{_format_ics_datetime(end)}",
        f"DTSTAMP:{_format_ics_datetime(now)}",
        f"SUMMARY:{_escape_ics_text(event.title)}",
    ]

    if event.description:
        lines.append(f"DESCRIPTION:{_escape_ics_text(event.description)}")

    if event.location:
        lines.append(f"LOCATION:{_escape_ics_text(event.location)}")

    if event.url:
        lines.append(f"URL:{event.url}")

    if event.organizer_email:
        organizer = f"ORGANIZER;CN={_escape_ics_text(event.organizer_name)}:mailto:{event.organizer_email}"
        lines.append(organizer)

    lines.extend([
        "STATUS:CONFIRMED",
        "END:VEVENT",
        "END:VCALENDAR",
    ])

    return "\r\n".join(lines)


def parse_datetime_flexible(date_str: str) -> Optional[datetime]:
    """Parse a datetime string in common formats.

    Supports:
      - ISO 8601: 2026-03-20T14:00:00
      - ISO date: 2026-03-20
      - With timezone offset: 2026-03-20T14:00:00-06:00

    Args:
        date_str: A date/datetime string.

    Returns:
        A datetime object, or None if parsing fails.
    """
    # Strip timezone offset for simplicity (treat as UTC-ish)
    date_str = re.sub(r'[+-]\d{2}:\d{2}$', '', date_str.strip())

    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    logger.warning(f"Could not parse datetime: {date_str}")
    return None
