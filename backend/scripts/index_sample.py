"""
Index sample documents for testing.
Run after init_db.py to populate the database with test data.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.connection import AsyncSessionLocal
from rag.service import IndexingService

# Sample Yale documents for testing
SAMPLE_DOCUMENTS = [
    {
        "url": "https://registrar.yale.edu/calendar/fall-2026",
        "title": "Academic Calendar - Fall 2026",
        "site": "registrar",
        "content": """
Academic Calendar Fall 2026

Important Dates:
- August 26, 2026: Classes begin
- September 2, 2026: Labor Day (no classes)
- September 15, 2026: Add/Drop deadline
- October 16-18, 2026: October recess
- November 1, 2026: Course withdrawal deadline
- November 25-29, 2026: Thanksgiving recess
- December 10, 2026: Classes end
- December 11-13, 2026: Reading period
- December 14-22, 2026: Final examinations

Registration:
Students should register for courses through the Yale Course Search system.
Course registration opens in April for the following fall semester.
First-year students register during Camp Yale orientation.

Add/Drop Period:
Students may add or drop courses without penalty until September 15, 2026.
After this date, courses may only be dropped with the instructor's permission.
The withdrawal deadline for courses is November 1, 2026.
        """,
    },
    {
        "url": "https://yalecollege.yale.edu/academics/credit-limit",
        "title": "Credit Limit Policy",
        "site": "yalecollege",
        "content": """
Credit Limit Policy

Standard Course Load:
Yale College students normally take four or five courses per term.
The standard range is 4.0 to 5.5 course credits per term.

Maximum Credit Limit:
Students may not exceed 6.0 course credits in a single term without permission.
Permission to exceed the credit limit must be obtained from the student's dean.

Minimum Credit Requirement:
Full-time students must enroll in at least 3.0 course credits per term.
Students taking fewer credits may be considered part-time.

Accelerated Programs:
Students in accelerated programs may have different credit requirements.
Consult with your academic advisor for specific requirements.
        """,
    },
    {
        "url": "https://dining.yale.edu/locations/commons",
        "title": "Commons Dining Hall",
        "site": "dining",
        "content": """
Commons Dining Hall

Location: On the Old Campus, adjacent to Beinecke Plaza

Hours of Operation:
- Breakfast: 7:30 AM - 10:00 AM (Monday-Friday)
- Lunch: 11:30 AM - 1:30 PM (Monday-Friday)
- Dinner: 5:00 PM - 7:30 PM (Monday-Thursday)
- Brunch: 10:30 AM - 1:30 PM (Saturday-Sunday)
- Dinner: 5:00 PM - 7:00 PM (Saturday-Sunday)

Features:
- All-you-care-to-eat dining
- Vegetarian and vegan options available
- Allergen-friendly stations
- Made-to-order grill items

Meal Plans:
Commons accepts all Yale dining meal plans.
Guests may purchase individual meals at the door.
        """,
    },
    {
        "url": "https://library.yale.edu/borrowing",
        "title": "Library Borrowing Policies",
        "site": "library",
        "content": """
Library Borrowing Policies

Loan Periods:
- Undergraduate students: 28 days, renewable up to 3 times
- Graduate students: 84 days, renewable up to 3 times
- Faculty: Term loan (entire semester)

Renewals:
Books may be renewed online through your library account.
Items with holds cannot be renewed.
Overdue items cannot be renewed until returned.

Fines:
- General collection: $0.25 per day overdue
- Reserve items: $1.00 per hour overdue
- Maximum fine: Replacement cost of item

Interlibrary Loan:
Yale students may borrow materials from other libraries through Borrow Direct.
Processing time is typically 4-7 business days.
        """,
    },
    {
        "url": "https://its.yale.edu/wifi",
        "title": "Yale Wireless Network (WiFi)",
        "site": "its",
        "content": """
Yale Wireless Network

Available Networks:
- YaleSecure: Primary network for Yale community members
- Yale Guest: Temporary access for visitors
- eduroam: For visiting scholars from other institutions

Connecting to YaleSecure:
1. Select "YaleSecure" from available networks
2. Enter your Yale NetID and password
3. Accept the certificate if prompted
4. You're connected!

Troubleshooting:
- Forget the network and reconnect
- Ensure your device's date and time are correct
- Check that your NetID password hasn't expired
- Contact the ITS Help Desk at 203-432-9000

Coverage:
YaleSecure is available in all academic buildings, residential colleges,
libraries, and most outdoor spaces on campus.
        """,
    },
]


async def index_samples():
    """Index sample documents"""
    print("Indexing sample documents...")
    print("=" * 50)

    indexing_service = IndexingService()
    total_chunks = 0

    async with AsyncSessionLocal() as session:
        for doc in SAMPLE_DOCUMENTS:
            import hashlib
            content_hash = hashlib.md5(doc["content"].encode()).hexdigest()

            print(f"\nIndexing: {doc['title']}")
            try:
                chunks = await indexing_service.index_document(
                    session=session,
                    url=doc["url"],
                    title=doc["title"],
                    content=doc["content"],
                    site=doc["site"],
                    content_hash=content_hash,
                )
                print(f"  Created {chunks} chunks")
                total_chunks += chunks
            except Exception as e:
                print(f"  Error: {e}")

    print("\n" + "=" * 50)
    print(f"Total documents indexed: {len(SAMPLE_DOCUMENTS)}")
    print(f"Total chunks created: {total_chunks}")
    print("\nSample data is ready. You can now test the chat endpoint.")


if __name__ == "__main__":
    asyncio.run(index_samples())
