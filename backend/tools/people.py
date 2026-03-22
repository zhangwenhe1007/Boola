"""
People lookup tool using Yalies.io API
"""
from dataclasses import dataclass
from typing import Optional
import httpx


@dataclass
class PersonResult:
    """Person lookup result"""
    name: str
    netid: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    college: Optional[str] = None
    year: Optional[int] = None
    url: Optional[str] = None


async def lookup_person(
    name: Optional[str] = None,
    netid: Optional[str] = None,
    department: Optional[str] = None,
) -> list[PersonResult]:
    """
    Search Yale directory via Yalies.io API.

    Args:
        name: Person's name to search
        netid: Yale NetID
        department: Department filter

    Returns:
        List of PersonResult objects
    """
    # TODO: Integrate with Yalies.io API
    # API docs: https://yalies.io/api
    # Endpoint: https://yalies.io/api/people

    # Placeholder for now
    if not any([name, netid, department]):
        return []

    return [
        PersonResult(
            name="Example Person",
            netid="abc123",
            email="example@yale.edu",
            department=department or "Computer Science",
            title="Professor",
            url="https://yalies.io/",
        )
    ]
