"""
Course search tool using Yale APIs
"""
from dataclasses import dataclass
from typing import Optional
import httpx


@dataclass
class CourseResult:
    """Course search result"""
    course_id: str
    title: str
    subject: str
    number: str
    term: str
    instructor: Optional[str] = None
    times: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None


async def find_courses(
    term: str,
    subject: Optional[str] = None,
    keyword: Optional[str] = None,
    time_filter: Optional[str] = None,
) -> list[CourseResult]:
    """
    Search Yale courses.

    Args:
        term: Academic term (e.g., "Fall 2026", "Spring 2026")
        subject: Subject code (e.g., "CPSC", "ECON")
        keyword: Search keyword in course title/description
        time_filter: Time preference (e.g., "morning", "afternoon")

    Returns:
        List of CourseResult objects
    """
    # TODO: Integrate with Yale Courses Web Service API
    # For now, return placeholder data
    # API endpoint: https://gw.its.yale.edu/soa-gateway/courses/webservice/v3/
    # Requires API key from Yale API Portal

    return [
        CourseResult(
            course_id="CPSC-223",
            title="Data Structures and Programming Techniques",
            subject="CPSC",
            number="223",
            term=term,
            instructor="TBD",
            times="TTh 1:00-2:15",
            location="WTS A60",
            url="https://courses.yale.edu/",
        )
    ]
