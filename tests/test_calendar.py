"""
Tests for desilo_core.utils.calendar

Run with: pytest tests/test_calendar.py -v
"""

from datetime import datetime
from desilo_core.utils.calendar import (
    CalendarEvent, generate_ics, parse_datetime_flexible,
    _escape_ics_text, _format_ics_datetime,
)


class TestGenerateIcs:
    """Tests for .ics file generation."""

    def test_basic_event(self):
        event = CalendarEvent(
            title="Demo Day",
            start=datetime(2026, 3, 20, 14, 0, 0),
        )
        ics = generate_ics(event)

        assert "BEGIN:VCALENDAR" in ics
        assert "END:VCALENDAR" in ics
        assert "BEGIN:VEVENT" in ics
        assert "SUMMARY:Demo Day" in ics
        assert "DTSTART:20260320T140000Z" in ics
        # Default 1 hour duration
        assert "DTEND:20260320T150000Z" in ics

    def test_event_with_all_fields(self):
        event = CalendarEvent(
            title="Startup Pitch Night",
            start=datetime(2026, 4, 10, 18, 0, 0),
            description="Join us for an evening of startup pitches",
            location="Distillery Labs, Peoria IL",
            url="https://example.com/events/pitch-night",
            duration_hours=2.5,
            organizer_name="Distillery Labs",
            organizer_email="events@distillerylabs.org",
        )
        ics = generate_ics(event)

        assert "SUMMARY:Startup Pitch Night" in ics
        assert "DTSTART:20260410T180000Z" in ics
        assert "DTEND:20260410T203000Z" in ics  # 18:00 + 2.5 hours
        assert "DESCRIPTION:Join us for an evening of startup pitches" in ics
        assert "LOCATION:Distillery Labs\\, Peoria IL" in ics
        assert "URL:https://example.com/events/pitch-night" in ics
        assert "ORGANIZER;CN=Distillery Labs:mailto:events@distillerylabs.org" in ics

    def test_ics_has_valid_structure(self):
        event = CalendarEvent(title="Test", start=datetime(2026, 1, 1))
        ics = generate_ics(event)

        assert ics.startswith("BEGIN:VCALENDAR")
        assert ics.endswith("END:VCALENDAR")
        assert "VERSION:2.0" in ics
        assert "METHOD:PUBLISH" in ics
        assert "STATUS:CONFIRMED" in ics

    def test_unique_uid_per_event(self):
        e1 = CalendarEvent(title="Event 1", start=datetime(2026, 1, 1))
        e2 = CalendarEvent(title="Event 2", start=datetime(2026, 1, 2))
        assert e1.uid != e2.uid

    def test_custom_uid(self):
        event = CalendarEvent(
            title="Test",
            start=datetime(2026, 1, 1),
            uid="custom-uid-123@desilo",
        )
        ics = generate_ics(event)
        assert "UID:custom-uid-123@desilo" in ics

    def test_crlf_line_endings(self):
        """iCalendar spec requires CRLF line endings."""
        event = CalendarEvent(title="Test", start=datetime(2026, 1, 1))
        ics = generate_ics(event)
        assert "\r\n" in ics

    def test_special_characters_escaped(self):
        event = CalendarEvent(
            title="Meet & Greet; Networking",
            start=datetime(2026, 1, 1),
            description="Line 1\nLine 2",
            location="Room 101, Building A",
        )
        ics = generate_ics(event)

        assert "SUMMARY:Meet & Greet\\; Networking" in ics
        assert "DESCRIPTION:Line 1\\nLine 2" in ics
        assert "LOCATION:Room 101\\, Building A" in ics


class TestEscapeIcsText:
    """Tests for iCalendar text escaping."""

    def test_escapes_semicolons(self):
        assert _escape_ics_text("a;b") == "a\\;b"

    def test_escapes_commas(self):
        assert _escape_ics_text("a,b") == "a\\,b"

    def test_escapes_newlines(self):
        assert _escape_ics_text("a\nb") == "a\\nb"

    def test_escapes_backslashes(self):
        assert _escape_ics_text("a\\b") == "a\\\\b"

    def test_plain_text_unchanged(self):
        assert _escape_ics_text("Hello World") == "Hello World"


class TestFormatIcsDatetime:
    """Tests for datetime formatting."""

    def test_formats_correctly(self):
        dt = datetime(2026, 3, 20, 14, 30, 0)
        assert _format_ics_datetime(dt) == "20260320T143000Z"

    def test_midnight(self):
        dt = datetime(2026, 1, 1, 0, 0, 0)
        assert _format_ics_datetime(dt) == "20260101T000000Z"


class TestParseDatetimeFlexible:
    """Tests for flexible datetime parsing."""

    def test_iso_datetime(self):
        dt = parse_datetime_flexible("2026-03-20T14:00:00")
        assert dt == datetime(2026, 3, 20, 14, 0, 0)

    def test_iso_date_only(self):
        dt = parse_datetime_flexible("2026-03-20")
        assert dt == datetime(2026, 3, 20)

    def test_with_timezone_offset(self):
        dt = parse_datetime_flexible("2026-03-20T14:00:00-06:00")
        assert dt == datetime(2026, 3, 20, 14, 0, 0)

    def test_us_date_format(self):
        dt = parse_datetime_flexible("03/20/2026")
        assert dt == datetime(2026, 3, 20)

    def test_full_month_name(self):
        dt = parse_datetime_flexible("March 20, 2026")
        assert dt == datetime(2026, 3, 20)

    def test_abbreviated_month(self):
        dt = parse_datetime_flexible("Mar 20, 2026")
        assert dt == datetime(2026, 3, 20)

    def test_invalid_returns_none(self):
        assert parse_datetime_flexible("not a date") is None

    def test_empty_string_returns_none(self):
        assert parse_datetime_flexible("") is None
