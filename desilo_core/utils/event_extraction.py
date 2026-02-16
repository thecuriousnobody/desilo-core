"""
Event Extraction Utilities

Generic functions for extracting structured event data from text.
Works with markdown tables, tagged items, and free-form text.
"""

import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def extract_events_from_markdown_table(text: str) -> List[Dict[str, str]]:
    """Extract events from a markdown table under an '## Upcoming Events' heading.

    Expected table format:
        | Date | Event | Organization | Location | Details |
        |------|-------|-------------|----------|---------|
        | Feb 18 | [AgTech Connect](url) | GPEDC | USDA Ag Lab | 10:00 AM |

    Returns list of dicts with keys:
        title, date, time, location, organization, organization_full,
        description, original_link, event_type
    """
    events: List[Dict[str, str]] = []

    table_section = re.search(
        r'## Upcoming Events\s*\n(.*?)(?=\n---|\n## |\Z)',
        text,
        re.DOTALL,
    )
    if not table_section:
        return events

    table_text = table_section.group(1)

    for row in table_text.strip().split('\n'):
        row = row.strip()
        if not row.startswith('|') or '---' in row:
            continue
        cells = [c.strip() for c in row.split('|')[1:-1]]
        if len(cells) < 4:
            continue
        if cells[0].lower() in ('date', 'dates'):
            continue

        date_str = cells[0].strip()
        event_cell = cells[1].strip()
        org = cells[2].strip() if len(cells) > 2 else ''
        location = cells[3].strip() if len(cells) > 3 else ''
        details = cells[4].strip() if len(cells) > 4 else ''

        # Extract title and link from markdown [Title](url) format
        link_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', event_cell)
        if link_match:
            title = link_match.group(1)
            link = link_match.group(2)
        else:
            title = event_cell
            link = ''

        if title:
            events.append({
                'title': title,
                'date': date_str,
                'time': details,
                'location': location,
                'organization': org,
                'organization_full': org,
                'description': f"{title} hosted by {org}" if org else title,
                'original_link': link,
                'event_type': 'event',
            })

    return events


def extract_tagged_events(text: str, tag: str = "EVENT") -> List[Dict[str, str]]:
    """Extract events from lines containing **[TAG]** markers.

    Scans for lines like:
        - **[EVENT]** [Title](url) - March 15th, 5:00 PM at Location

    Args:
        text: Raw text to scan.
        tag: The tag to look for (default "EVENT").

    Returns list of dicts with the same keys as extract_events_from_markdown_table.
    """
    events: List[Dict[str, str]] = []
    tag_pattern = f'**[{tag}]**'
    current_section = ''

    for line in text.split('\n'):
        # Track section headers
        header_match = re.match(r'^## (.+)', line)
        if header_match:
            current_section = header_match.group(1).strip()
            continue

        if tag_pattern not in line:
            continue

        # Extract title and link
        link_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', line)
        if link_match:
            title = link_match.group(1)
            link = link_match.group(2)
        else:
            escaped_tag = re.escape(tag)
            title_match = re.search(
                rf'\*\*\[{escaped_tag}\]\*\*\s*(.+?)(?:\s*-\s*|$)', line
            )
            title = title_match.group(1).strip() if title_match else ''
            link = ''

        if not title:
            continue

        # Parse remainder for date, time, location
        remainder = line.split(title, 1)[-1] if title in line else ''
        remainder = re.sub(r'\]\([^)]+\)', '', remainder)
        remainder = remainder.strip(' -,')

        date_str = ''
        time_str = ''
        loc = ''

        at_match = re.search(r'\bat\b\s+(.+)', remainder)
        if at_match:
            loc = at_match.group(1).strip()
            remainder = remainder[:at_match.start()].strip(' -,')

        time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))', remainder)
        if time_match:
            time_str = time_match.group(1)
            remainder = remainder.replace(time_match.group(0), '').strip(' -,')

        date_str = remainder.strip(' -,')

        events.append({
            'title': title,
            'date': date_str,
            'time': time_str,
            'location': loc,
            'organization': current_section,
            'organization_full': current_section,
            'description': (
                f"{title} hosted by {current_section}"
                if current_section
                else title
            ),
            'original_link': link,
            'event_type': 'event',
        })

    return events


def extract_events(text: str) -> List[Dict[str, str]]:
    """Extract all events from text, combining multiple extraction methods.

    Parses both markdown tables and tagged items, deduplicates by title.

    Args:
        text: Raw markdown/text containing event information.

    Returns:
        Deduplicated list of event dicts.
    """
    seen_titles: set = set()
    all_events: List[Dict[str, str]] = []

    # Source 1: Markdown tables
    table_events = extract_events_from_markdown_table(text)
    for event in table_events:
        key = event['title'].lower()
        if key not in seen_titles:
            seen_titles.add(key)
            all_events.append(event)

    # Source 2: Tagged items
    tagged_events = extract_tagged_events(text)
    for event in tagged_events:
        key = event['title'].lower()
        if key not in seen_titles:
            seen_titles.add(key)
            all_events.append(event)

    table_count = len(table_events)
    tagged_count = len(tagged_events)
    logger.info(
        f"Extracted {len(all_events)} events "
        f"(table: {table_count}, tagged: {tagged_count})"
    )

    return all_events
