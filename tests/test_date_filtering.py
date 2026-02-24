"""
Tests for desilo_core.utils.date_filtering

Run with: pytest tests/test_date_filtering.py -v
"""

from datetime import datetime
from desilo_core.utils.date_filtering import filter_past_events, extract_dates_from_text


class TestExtractDatesFromText:
    """Tests for the extract_dates_from_text helper."""

    def test_extracts_iso_dates(self):
        dates = extract_dates_from_text("Event on 2026-03-20 at the hub")
        assert len(dates) == 1
        assert dates[0] == datetime(2026, 3, 20)

    def test_extracts_full_month_dates(self):
        dates = extract_dates_from_text("Workshop on March 20, 2026")
        assert len(dates) == 1
        assert dates[0] == datetime(2026, 3, 20)

    def test_extracts_abbreviated_month_dates(self):
        dates = extract_dates_from_text("Meetup on Mar 20, 2026")
        assert len(dates) == 1
        assert dates[0] == datetime(2026, 3, 20)

    def test_extracts_multiple_dates(self):
        dates = extract_dates_from_text("From 2026-01-10 to 2026-01-15")
        assert len(dates) == 2

    def test_returns_empty_for_no_dates(self):
        dates = extract_dates_from_text("No dates in this text")
        assert dates == []

    def test_handles_date_without_comma(self):
        dates = extract_dates_from_text("Event on March 20 2026")
        assert len(dates) == 1
        assert dates[0] == datetime(2026, 3, 20)

    def test_case_insensitive(self):
        dates = extract_dates_from_text("Event on MARCH 20, 2026")
        assert len(dates) == 1
        assert dates[0] == datetime(2026, 3, 20)


class TestFilterPastEvents:
    """Tests for the filter_past_events function."""

    def test_filters_past_iso_dates(self):
        current_date = "2026-02-04"
        search_results = """
Event 1: Tech Meetup 2024-10-15 at the hub
Event 2: Startup Weekend 2026-03-20 coming up
Event 3: AI Workshop 2025-12-01 was great
Event 4: Funding Summit 2026-02-10 coming soon
"""
        filtered = filter_past_events(search_results, current_date)

        assert "2024-10-15" not in filtered
        assert "2025-12-01" not in filtered
        assert "2026-03-20" in filtered
        assert "2026-02-10" in filtered

    def test_filters_past_month_name_dates(self):
        current_date = "2026-02-04"
        search_results = """
Event: October 15, 2024 - Innovation Conference
Event: March 20, 2026 - Startup Pitch Night
Event: January 5, 2025 - New Year Kickoff
Event: December 15, 2026 - Holiday Tech Bash
"""
        filtered = filter_past_events(search_results, current_date)

        assert "October 15, 2024" not in filtered
        assert "January 5, 2025" not in filtered
        assert "March 20, 2026" in filtered
        assert "December 15, 2026" in filtered

    def test_filters_abbreviated_month_dates(self):
        current_date = "2026-02-04"
        search_results = """
Oct 15, 2024 - Old event
Mar 20, 2026 - Upcoming event
Aug 10, 2025 - Another past event
Jun 5, 2026 - Summer workshop
"""
        filtered = filter_past_events(search_results, current_date)

        assert "Oct 15, 2024" not in filtered
        assert "Aug 10, 2025" not in filtered
        assert "Mar 20, 2026" in filtered
        assert "Jun 5, 2026" in filtered

    def test_preserves_non_date_content(self):
        current_date = "2026-02-04"
        search_results = """
A startup hub in the midwest.
They host regular events and workshops.
Contact: info@example.com
Website: https://example.com
"""
        filtered = filter_past_events(search_results, current_date)

        assert "startup hub in the midwest" in filtered
        assert "regular events and workshops" in filtered
        assert "info@example.com" in filtered

    def test_handles_none_input(self):
        assert filter_past_events(None, "2026-02-04") is None

    def test_handles_empty_input(self):
        assert filter_past_events("", "2026-02-04") == ""

    def test_handles_mixed_content(self):
        current_date = "2026-02-04"
        search_results = """
Upcoming Events:
1. 2024-11-15 - Pitch Night (past)
2. Networking Happy Hour - No date specified
3. 2026-04-20 - Spring Demo Day
4. Weekly office hours every Tuesday
5. November 30, 2025 - Fall Showcase (past)
6. April 10, 2026 - Innovation Summit
"""
        filtered = filter_past_events(search_results, current_date)

        assert "Upcoming Events" in filtered
        assert "2024-11-15" not in filtered
        assert "November 30, 2025" not in filtered
        assert "2026-04-20" in filtered
        assert "April 10, 2026" in filtered
        assert "Networking Happy Hour" in filtered
        assert "Weekly office hours" in filtered

    def test_today_is_not_filtered(self):
        current_date = "2026-02-04"
        search_results = """
Event happening today: 2026-02-04 - Morning Workshop
Event tomorrow: 2026-02-05 - Tech Talk
Event yesterday: 2026-02-03 - Should be filtered
"""
        filtered = filter_past_events(search_results, current_date)

        assert "2026-02-04" in filtered, "Today's date should remain"
        assert "2026-02-05" in filtered, "Tomorrow should remain"
        assert "2026-02-03" not in filtered, "Yesterday should be filtered"

    def test_real_world_search_results(self):
        current_date = "2026-02-04"
        search_results = """
Search results for "startup events":

1. Startup Hub - Events Calendar
   https://example.com/events
   Join us for startup events

2. Past Event: AI Meeting - October 10, 2024
   https://example.com/events/ai-oct-2024
   Recording available from our October meetup

3. Upcoming: Spring Showcase - March 15, 2026
   https://example.com/events/spring-2026
   Register now for our annual showcase

4. Weekly Events: Office Hours every Tuesday
   Drop in for free mentorship sessions

5. Innovation Summit 2025-08-20 - Event Recap
   https://example.com/blog/summit-2025-recap
   Photos and highlights from our summer summit
"""
        filtered = filter_past_events(search_results, current_date)

        assert "October 10, 2024" not in filtered
        assert "2025-08-20" not in filtered
        assert "March 15, 2026" in filtered
        assert "Weekly Events: Office Hours" in filtered

    def test_invalid_current_date_returns_unfiltered(self):
        """If current_date is malformed, return results unchanged."""
        search_results = "Event: 2024-01-01 - Old event"
        filtered = filter_past_events(search_results, "not-a-date")
        assert filtered == search_results
