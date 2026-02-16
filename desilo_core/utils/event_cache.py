"""
Event Cache Utilities

Generic formatting functions for injecting cached event data
into chat agent prompts.
"""

from typing import List, Dict, Any


def format_events_for_prompt(events: List[Dict[str, Any]]) -> str:
    """Format cached events as a context string for an LLM prompt.

    Returns a human-readable list that a chat agent can parse and
    convert into structured event blocks for the frontend.

    Args:
        events: List of event dicts (as returned by EventStore.get_upcoming_events).

    Returns:
        Formatted string, or empty string if no events.
    """
    if not events:
        return ""

    lines = []
    for e in events:
        parts = [e.get('title', 'Untitled')]
        if e.get('date'):
            parts.append(f"Date: {e['date']}")
        if e.get('time'):
            parts.append(f"Time: {e['time']}")
        if e.get('organization_full') or e.get('organization'):
            parts.append(
                f"Org: {e.get('organization_full') or e['organization']}"
            )
        if e.get('location'):
            parts.append(f"Location: {e['location']}")
        if e.get('original_link'):
            parts.append(f"Link: {e['original_link']}")
        if e.get('description'):
            parts.append(f"Description: {e['description']}")
        lines.append(" | ".join(parts))

    return "\n".join(lines)
