"""
DeSilo Core Utilities

Generic helper functions for startup intelligence platforms.
"""

from .date_filtering import filter_past_events, extract_dates_from_text

__all__ = [
    'filter_past_events',
    'extract_dates_from_text',
]
