"""
Academic calendar tool
"""
from dataclasses import dataclass
from typing import Optional
from datetime import date


@dataclass
class CalendarEvent:
    """Academic calendar event"""
    event_type: str
    title: str
    date: str
    term: str
    description: Optional[str] = None
    url: Optional[str] = None


# Static calendar data (will be populated by crawler)
ACADEMIC_CALENDAR = {
    "Fall 2026": {
        "add_drop": CalendarEvent(
            event_type="add_drop",
            title="Add/Drop Deadline",
            date="2026-09-15",
            term="Fall 2026",
            description="Last day to add or drop courses without penalty",
            url="https://registrar.yale.edu/calendar",
        ),
        "withdrawal": CalendarEvent(
            event_type="withdrawal",
            title="Course Withdrawal Deadline",
            date="2026-11-01",
            term="Fall 2026",
            description="Last day to withdraw from courses",
            url="https://registrar.yale.edu/calendar",
        ),
        "reading_period": CalendarEvent(
            event_type="reading_period",
            title="Reading Period Begins",
            date="2026-12-10",
            term="Fall 2026",
            description="Classes end, reading period begins",
            url="https://registrar.yale.edu/calendar",
        ),
        "finals_start": CalendarEvent(
            event_type="finals_start",
            title="Final Examinations Begin",
            date="2026-12-14",
            term="Fall 2026",
            url="https://registrar.yale.edu/calendar",
        ),
    },
}


async def get_deadline(
    event_type: str,
    term: Optional[str] = None,
) -> Optional[CalendarEvent]:
    """
    Get academic deadline or event.

    Args:
        event_type: Type of event (add_drop, withdrawal, finals_start, etc.)
        term: Academic term (defaults to current term)

    Returns:
        CalendarEvent if found, None otherwise
    """
    # Default to current/upcoming term
    if term is None:
        # Determine current term based on date
        today = date.today()
        if today.month >= 8:
            term = f"Fall {today.year}"
        elif today.month >= 1 and today.month < 6:
            term = f"Spring {today.year}"
        else:
            term = f"Fall {today.year}"

    term_events = ACADEMIC_CALENDAR.get(term, {})
    return term_events.get(event_type)
