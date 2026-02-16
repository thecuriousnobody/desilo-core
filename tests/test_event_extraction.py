"""Tests for event extraction utilities."""

import pytest
from desilo_core.utils.event_extraction import (
    extract_events_from_markdown_table,
    extract_tagged_events,
    extract_events,
)


SAMPLE_BRIEF = """# Central Illinois ESO Media Brief

## Upcoming Events

| Date | Event | Organization | Location | Details |
|------|-------|-------------|----------|---------|
| Feb 18, 2026 | [AgTech Connect](https://instagram.com/p/123/) | Greater Peoria EDC | USDA Ag Lab, Peoria | 10:00-11:30 AM |
| Feb 18, 2026 | [Credit Game Workshop](https://instagram.com/p/456/) | MBDC | MBDC Office | 6:00-8:00 PM |
| Mar 18, 2026 | [Fail Club: Christell Frausto](https://facebook.com/events/789/) | Distillery Labs | 201 SW Adams St | 4:30-6:00 PM |

---

## Greater Peoria EDC

- **[EVENT]** [AgTech Connect](https://instagram.com/p/123/) - Feb 18, 10:00 AM at USDA Ag Lab

## Distillery Labs

- **[EVENT]** [Fail Club: Christell Frausto](https://facebook.com/events/789/) - March 18th, 4:30 PM at Distillery Labs Main Lobby
- **[PROMOTIONAL]** Check out our new website!
"""


class TestExtractEventsFromMarkdownTable:
    def test_basic_extraction(self):
        events = extract_events_from_markdown_table(SAMPLE_BRIEF)
        assert len(events) == 3

    def test_extracts_title(self):
        events = extract_events_from_markdown_table(SAMPLE_BRIEF)
        titles = [e['title'] for e in events]
        assert 'AgTech Connect' in titles
        assert 'Credit Game Workshop' in titles
        assert 'Fail Club: Christell Frausto' in titles

    def test_extracts_link(self):
        events = extract_events_from_markdown_table(SAMPLE_BRIEF)
        agtech = next(e for e in events if 'AgTech' in e['title'])
        assert agtech['original_link'] == 'https://instagram.com/p/123/'

    def test_extracts_organization(self):
        events = extract_events_from_markdown_table(SAMPLE_BRIEF)
        agtech = next(e for e in events if 'AgTech' in e['title'])
        assert agtech['organization'] == 'Greater Peoria EDC'

    def test_extracts_location(self):
        events = extract_events_from_markdown_table(SAMPLE_BRIEF)
        agtech = next(e for e in events if 'AgTech' in e['title'])
        assert 'USDA Ag Lab' in agtech['location']

    def test_no_table_returns_empty(self):
        events = extract_events_from_markdown_table("No table here")
        assert events == []

    def test_plain_text_event_no_link(self):
        text = """## Upcoming Events

| Date | Event | Organization | Location | Details |
|------|-------|-------------|----------|---------|
| Feb 20 | Open House | SomeCo | Main St | 2:00 PM |
"""
        events = extract_events_from_markdown_table(text)
        assert len(events) == 1
        assert events[0]['title'] == 'Open House'
        assert events[0]['original_link'] == ''


class TestExtractTaggedEvents:
    def test_basic_extraction(self):
        events = extract_tagged_events(SAMPLE_BRIEF)
        assert len(events) == 2  # Only EVENT tagged, not PROMOTIONAL

    def test_extracts_title_and_link(self):
        events = extract_tagged_events(SAMPLE_BRIEF)
        agtech = next(e for e in events if 'AgTech' in e['title'])
        assert agtech['original_link'] == 'https://instagram.com/p/123/'

    def test_tracks_section_as_org(self):
        events = extract_tagged_events(SAMPLE_BRIEF)
        fail_club = next(e for e in events if 'Fail Club' in e['title'])
        assert fail_club['organization'] == 'Distillery Labs'

    def test_ignores_non_event_tags(self):
        events = extract_tagged_events(SAMPLE_BRIEF, tag="PROMOTIONAL")
        # PROMOTIONAL items have different parsing; just verify no crash
        assert isinstance(events, list)

    def test_no_tagged_items_returns_empty(self):
        events = extract_tagged_events("Just some text without tags")
        assert events == []


class TestExtractEvents:
    def test_combines_both_sources(self):
        events = extract_events(SAMPLE_BRIEF)
        # 3 from table + 0 new from tagged (AgTech + Fail Club are dupes)
        assert len(events) == 3

    def test_deduplicates_by_title(self):
        events = extract_events(SAMPLE_BRIEF)
        titles = [e['title'].lower() for e in events]
        assert len(titles) == len(set(titles))

    def test_empty_text(self):
        events = extract_events("")
        assert events == []

    def test_returns_list_of_dicts(self):
        events = extract_events(SAMPLE_BRIEF)
        for e in events:
            assert isinstance(e, dict)
            assert 'title' in e
            assert 'date' in e
            assert 'organization' in e
