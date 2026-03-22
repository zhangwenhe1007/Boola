"""
Quick test for the Yale crawler.
Tests crawling a single page to verify everything works.
"""
import asyncio
from spiders.yale_crawler import YaleCrawler, CrawledPage


async def test_single_page():
    """Test crawling a single Yale page"""
    print("Testing Yale Crawler...")
    print("=" * 50)

    crawler = YaleCrawler(
        max_depth=0,  # Only seed URLs
        max_pages_per_site=1,
        delay_between_requests=0.1,
    )

    # Test with a simple Yale page
    test_urls = ["https://registrar.yale.edu/calendar"]

    pages = await crawler.crawl_site("test", test_urls)

    if pages:
        page = pages[0]
        print(f"\nSuccess! Crawled page:")
        print(f"  URL: {page.url}")
        print(f"  Title: {page.title}")
        print(f"  Site: {page.site}")
        print(f"  Content length: {len(page.content)} chars")
        print(f"  Hash: {page.content_hash}")
        print(f"\nContent preview:")
        print("-" * 40)
        print(page.content[:500] + "..." if len(page.content) > 500 else page.content)
        print("-" * 40)
        return True
    else:
        print("\nFailed to crawl any pages!")
        return False


async def test_link_extraction():
    """Test that link extraction works"""
    print("\n\nTesting link extraction...")
    print("=" * 50)

    crawler = YaleCrawler(
        max_depth=1,
        max_pages_per_site=5,
        delay_between_requests=0.2,
    )

    # Test with registrar (should find internal links)
    pages = await crawler.crawl_site("registrar", ["https://registrar.yale.edu/"])

    print(f"\nCrawled {len(pages)} pages with depth=1")
    for page in pages:
        print(f"  - {page.title[:50]}")

    return len(pages) > 1  # Should find more than just the seed URL


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("YALE CRAWLER TEST SUITE")
    print("=" * 60)

    results = []

    # Test 1: Single page
    results.append(("Single page crawl", await test_single_page()))

    # Test 2: Link extraction (only if single page works)
    if results[0][1]:
        results.append(("Link extraction", await test_link_extraction()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")

    all_passed = all(r[1] for r in results)
    print("\n" + ("All tests passed!" if all_passed else "Some tests failed!"))
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
