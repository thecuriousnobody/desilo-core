"""
Date Filtering Utilities

Post-processing utilities to filter past events from search results,
scraped content, or any text containing dated references. Useful for
ensuring users only see current and upcoming events.

Supports multiple date formats:
  - ISO: 2026-02-15
  - Full month: February 15, 2026
  - Abbreviated month: Feb 15, 2026
"""

import re
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

MONTH_MAP = {
    'january': 1, 'jan': 1,
    'february': 2, 'feb': 2,
    'march': 3, 'mar': 3,
    'april': 4, 'apr': 4,
    'may': 5,
    'june': 6, 'jun': 6,
    'july': 7, 'jul': 7,
    'august': 8, 'aug': 8,
    'september': 9, 'sep': 9,
    'october': 10, 'oct': 10,
    'november': 11, 'nov': 11,
    'december': 12, 'dec': 12,
}

# Regex for ISO format: YYYY-MM-DD
ISO_DATE_PATTERN = re.compile(r'(\d{4})-(\d{1,2})-(\d{1,2})')

# Regex for month name format: Month DD, YYYY or Mon DD, YYYY
MONTH_NAME_PATTERN = re.compile(
    r'(January|February|March|April|May|June|July|August|September|October|November|December|'
    r'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})',
    re.IGNORECASE
)


def extract_dates_from_text(text: str) -> list[datetime]:
    """Extract all recognizable dates from a line of text.

    Args:
        text: A string that may contain dates in various formats.

    Returns:
        List of datetime objects found in the text.
    """
    dates = []

    for match in ISO_DATE_PATTERN.finditer(text):
        try:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            dates.append(datetime(year, month, day))
        except ValueError:
            pass

    for match in MONTH_NAME_PATTERN.finditer(text):
        try:
            month_name = match.group(1).lower()
            day = int(match.group(2))
            year = int(match.group(3))
            month = MONTH_MAP.get(month_name, 0)
            if month:
                dates.append(datetime(year, month, day))
        except ValueError:
            pass

    return dates


def filter_past_events(search_results: Optional[str], current_date: str) -> Optional[str]:
    """Filter out lines containing past dates from search results.

    Post-processing step to ensure past events don't appear in search
    results, even if the search API returns them. Lines without
    recognizable dates are always preserved. Today's date is NOT
    considered past — events happening today are kept.

    Args:
        search_results: Raw search results string (newline-separated).
        current_date: Current date in YYYY-MM-DD format.

    Returns:
        Filtered search results with past event lines removed.
        Returns None if input is None, empty string if input is empty.
    """
    if search_results is None:
        return None
    if not search_results:
        return search_results

    try:
        current = datetime.strptime(current_date, "%Y-%m-%d")
    except ValueError:
        logger.error(f"Invalid current_date format: {current_date}. Expected YYYY-MM-DD.")
        return search_results

    lines = search_results.split('\n')
    filtered_lines = []

    for line in lines:
        dates_in_line = extract_dates_from_text(line)

        # If any date in the line is in the past, filter the whole line
        has_past_date = any(d < current for d in dates_in_line)

        if has_past_date:
            logger.debug(f"Filtering past event: {line[:80]}...")
        else:
            filtered_lines.append(line)

    filtered_results = '\n'.join(filtered_lines)
    original_count = len(lines)
    filtered_count = len(filtered_lines)
    if original_count != filtered_count:
        logger.info(f"Date filtering: {original_count} lines -> {filtered_count} lines")

    return filtered_results
