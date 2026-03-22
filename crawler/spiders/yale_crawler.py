"""
Yale website crawler for RAG indexing.

Crawls Yale websites, extracts content, and can send to backend for indexing.
Respects robots.txt and implements polite crawling with rate limiting.
"""
import hashlib
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse, urljoin
import asyncio
import logging

import httpx
import trafilatura
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class CrawledPage:
    """Represents a crawled web page"""
    url: str
    title: str
    content: str
    site: str
    content_hash: str
    crawled_at: str  # ISO format string for JSON serialization

    def to_dict(self) -> dict:
        """Convert to dictionary for API submission"""
        return asdict(self)


# Seed URLs for Yale websites organized by category
SEED_URLS = {
    "registrar": [
        "https://registrar.yale.edu/",
        "https://registrar.yale.edu/calendar",
        "https://registrar.yale.edu/registration-and-enrollment",
        "https://registrar.yale.edu/forms-petitions",
        "https://registrar.yale.edu/course-related-petitions",
        "https://registrar.yale.edu/students",
    ],
    "yalecollege": [
        "https://yalecollege.yale.edu/",
        "https://yalecollege.yale.edu/academics",
        "https://yalecollege.yale.edu/campus-life",
        "https://yalecollege.yale.edu/academics/academic-requirements",
        "https://yalecollege.yale.edu/academics/faculty-advising",
    ],
    "dining": [
        "https://dining.yale.edu/",
        "https://dining.yale.edu/locations",
        "https://dining.yale.edu/menus",
    ],
    "library": [
        "https://library.yale.edu/",
        "https://library.yale.edu/help",
        "https://library.yale.edu/services",
        "https://library.yale.edu/research-support",
    ],
    "its": [
        "https://its.yale.edu/",
        "https://its.yale.edu/services",
        "https://its.yale.edu/support",
        "https://its.yale.edu/how-to",
    ],
    "studentlife": [
        "https://studentlife.yale.edu/",
        "https://studentlife.yale.edu/resources",
    ],
}

# URL patterns to exclude from crawling
EXCLUDE_PATTERNS = [
    r'/login',
    r'/logout',
    r'/auth',
    r'/search\?',
    r'/print/',
    r'\.pdf$',
    r'\.doc[x]?$',
    r'\.xls[x]?$',
    r'\.ppt[x]?$',
    r'\.zip$',
    r'\.jpg$',
    r'\.png$',
    r'\.gif$',
    r'/feed/',
    r'/rss/',
    r'\?page=',
    r'#',  # Fragment identifiers
]


class RobotsChecker:
    """Simple robots.txt checker"""

    def __init__(self):
        self.rules: dict[str, list[str]] = {}  # domain -> disallowed paths
        self.checked: set[str] = set()

    async def fetch_robots(self, client: httpx.AsyncClient, domain: str):
        """Fetch and parse robots.txt for a domain"""
        if domain in self.checked:
            return

        self.checked.add(domain)
        robots_url = f"https://{domain}/robots.txt"

        try:
            response = await client.get(robots_url, timeout=10.0)
            if response.status_code == 200:
                disallowed = []
                for line in response.text.split('\n'):
                    line = line.strip().lower()
                    if line.startswith('disallow:'):
                        path = line.split(':', 1)[1].strip()
                        if path:
                            disallowed.append(path)
                self.rules[domain] = disallowed
                logger.debug(f"Loaded robots.txt for {domain}: {len(disallowed)} rules")
        except Exception as e:
            logger.debug(f"Could not fetch robots.txt for {domain}: {e}")
            self.rules[domain] = []

    def is_allowed(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt"""
        parsed = urlparse(url)
        domain = parsed.netloc
        path = parsed.path.lower()

        if domain not in self.rules:
            return True  # Assume allowed if not checked

        for disallowed in self.rules.get(domain, []):
            if path.startswith(disallowed):
                return False

        return True


class YaleCrawler:
    """
    Crawler for Yale websites with robots.txt compliance.

    Features:
    - Respects robots.txt
    - Extracts links for deeper crawling
    - Rate limiting to be polite
    - Filters out non-content URLs
    """

    def __init__(
        self,
        max_depth: int = 2,
        max_pages_per_site: int = 50,
        timeout: float = 30.0,
        delay_between_requests: float = 0.5,
    ):
        """
        Initialize crawler.

        Args:
            max_depth: Maximum crawl depth from seed URLs
            max_pages_per_site: Maximum pages to crawl per site
            timeout: Request timeout in seconds
            delay_between_requests: Delay between requests in seconds
        """
        self.max_depth = max_depth
        self.max_pages_per_site = max_pages_per_site
        self.timeout = timeout
        self.delay = delay_between_requests
        self.visited: set[str] = set()
        self.robots = RobotsChecker()

    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and trailing slashes"""
        parsed = urlparse(url)
        # Remove fragment
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        # Remove trailing slash (except for root)
        if normalized.endswith('/') and parsed.path != '/':
            normalized = normalized[:-1]
        return normalized

    def _should_crawl(self, url: str, base_domain: str) -> bool:
        """Check if URL should be crawled"""
        parsed = urlparse(url)

        # Must be same domain or subdomain of yale.edu
        if not parsed.netloc.endswith('yale.edu'):
            return False

        # Must be HTTP(S)
        if parsed.scheme not in ('http', 'https'):
            return False

        # Check exclude patterns
        for pattern in EXCLUDE_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return False

        # Already visited
        if self._normalize_url(url) in self.visited:
            return False

        return True

    def _extract_links(self, html: str, base_url: str) -> list[str]:
        """Extract links from HTML content"""
        links = []
        try:
            soup = BeautifulSoup(html, 'lxml')
            base_domain = urlparse(base_url).netloc

            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']

                # Convert relative to absolute URL
                absolute_url = urljoin(base_url, href)
                normalized = self._normalize_url(absolute_url)

                if self._should_crawl(normalized, base_domain):
                    links.append(normalized)

        except Exception as e:
            logger.debug(f"Error extracting links from {base_url}: {e}")

        return list(set(links))  # Remove duplicates

    def _extract_title(self, html: str, url: str) -> str:
        """Extract page title from HTML"""
        try:
            soup = BeautifulSoup(html, 'lxml')

            # Try <title> tag
            title_tag = soup.find('title')
            if title_tag and title_tag.string:
                title = title_tag.string.strip()
                # Remove common suffixes
                for suffix in [' | Yale University', ' - Yale', ' | Yale']:
                    if title.endswith(suffix):
                        title = title[:-len(suffix)]
                return title

            # Try <h1> tag
            h1_tag = soup.find('h1')
            if h1_tag:
                return h1_tag.get_text().strip()

        except Exception:
            pass

        # Fallback to URL path
        path = urlparse(url).path.strip('/')
        return path.replace('-', ' ').replace('/', ' > ').title() or 'Untitled'

    def _determine_site(self, url: str) -> str:
        """Determine site category from URL"""
        domain = urlparse(url).netloc

        # Map subdomains to categories
        subdomain = domain.replace('.yale.edu', '')

        # Handle common patterns
        site_mapping = {
            'registrar': 'registrar',
            'yalecollege': 'yalecollege',
            'dining': 'dining',
            'library': 'library',
            'its': 'its',
            'studentlife': 'studentlife',
            'athletics': 'athletics',
            'admissions': 'admissions',
            'www': 'yale',
        }

        return site_mapping.get(subdomain, subdomain)

    async def crawl_page(
        self,
        client: httpx.AsyncClient,
        url: str,
    ) -> tuple[Optional[CrawledPage], list[str]]:
        """
        Crawl a single page.

        Args:
            client: HTTP client
            url: URL to crawl

        Returns:
            Tuple of (CrawledPage or None, list of extracted links)
        """
        normalized_url = self._normalize_url(url)

        if normalized_url in self.visited:
            return None, []

        # Check robots.txt
        domain = urlparse(url).netloc
        await self.robots.fetch_robots(client, domain)
        if not self.robots.is_allowed(url):
            logger.info(f"Blocked by robots.txt: {url}")
            return None, []

        self.visited.add(normalized_url)

        try:
            response = await client.get(
                url,
                timeout=self.timeout,
                follow_redirects=True,
            )

            if response.status_code != 200:
                logger.debug(f"Non-200 status for {url}: {response.status_code}")
                return None, []

            # Check content type
            content_type = response.headers.get('content-type', '')
            if 'text/html' not in content_type:
                logger.debug(f"Skipping non-HTML content: {url}")
                return None, []

            html = response.text

            # Extract main content using trafilatura
            content = trafilatura.extract(
                html,
                include_links=False,
                include_tables=True,
                include_comments=False,
                no_fallback=False,
            )

            if not content or len(content) < 100:
                logger.debug(f"Insufficient content from {url}")
                return None, []

            # Extract metadata
            title = self._extract_title(html, url)
            site = self._determine_site(url)
            content_hash = hashlib.md5(content.encode()).hexdigest()

            # Extract links for further crawling
            links = self._extract_links(html, url)

            page = CrawledPage(
                url=normalized_url,
                title=title,
                content=content,
                site=site,
                content_hash=content_hash,
                crawled_at=datetime.now(timezone.utc).isoformat(),
            )

            return page, links

        except httpx.TimeoutException:
            logger.warning(f"Timeout crawling {url}")
            return None, []
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return None, []

    async def crawl_site(
        self,
        site_name: str,
        seed_urls: list[str],
    ) -> list[CrawledPage]:
        """
        Crawl a site starting from seed URLs with BFS.

        Args:
            site_name: Name of the site (for logging)
            seed_urls: List of starting URLs

        Returns:
            List of crawled pages
        """
        pages: list[CrawledPage] = []
        queue: list[tuple[str, int]] = [(url, 0) for url in seed_urls]

        async with httpx.AsyncClient(
            headers={
                'User-Agent': 'BoolaBot/1.0 (Yale Student Project; educational purposes)',
                'Accept': 'text/html,application/xhtml+xml',
            }
        ) as client:
            while queue and len(pages) < self.max_pages_per_site:
                url, depth = queue.pop(0)

                if depth > self.max_depth:
                    continue

                # Rate limiting
                await asyncio.sleep(self.delay)

                page, links = await self.crawl_page(client, url)

                if page:
                    pages.append(page)
                    logger.info(f"[{site_name}] ({len(pages)}) {page.title[:60]}")

                    # Add new links to queue
                    if depth < self.max_depth:
                        for link in links:
                            if self._normalize_url(link) not in self.visited:
                                queue.append((link, depth + 1))

        return pages

    async def crawl_all(
        self,
        sites: Optional[list[str]] = None,
    ) -> list[CrawledPage]:
        """
        Crawl all configured Yale sites.

        Args:
            sites: Optional list of site names to crawl (defaults to all)

        Returns:
            List of all crawled pages
        """
        all_pages: list[CrawledPage] = []

        sites_to_crawl = sites or list(SEED_URLS.keys())

        for site_name in sites_to_crawl:
            if site_name not in SEED_URLS:
                logger.warning(f"Unknown site: {site_name}")
                continue

            seed_urls = SEED_URLS[site_name]
            logger.info(f"\n{'='*50}")
            logger.info(f"Crawling {site_name} ({len(seed_urls)} seed URLs)...")
            logger.info(f"{'='*50}")

            pages = await self.crawl_site(site_name, seed_urls)
            all_pages.extend(pages)

            logger.info(f"Finished {site_name}: {len(pages)} pages crawled")

        logger.info(f"\n{'='*50}")
        logger.info(f"TOTAL: {len(all_pages)} pages crawled")
        logger.info(f"{'='*50}")

        return all_pages


class BackendIndexer:
    """Send crawled pages to the backend API for indexing"""

    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url

    async def index_page(self, page: CrawledPage) -> bool:
        """Index a single page via the backend API"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.backend_url}/index",
                    json={
                        "url": page.url,
                        "title": page.title,
                        "content": page.content,
                        "site": page.site,
                        "content_hash": page.content_hash,
                    },
                    timeout=60.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    logger.debug(f"Indexed: {page.title} ({data.get('chunks_created', 0)} chunks)")
                    return True
                else:
                    logger.error(f"Failed to index {page.url}: {response.status_code}")
                    return False
            except Exception as e:
                logger.error(f"Error indexing {page.url}: {e}")
                return False

    async def index_pages(self, pages: list[CrawledPage]) -> tuple[int, int]:
        """
        Index multiple pages.

        Returns:
            Tuple of (success_count, failure_count)
        """
        success = 0
        failed = 0

        for i, page in enumerate(pages):
            logger.info(f"Indexing [{i+1}/{len(pages)}]: {page.title[:50]}...")
            if await self.index_page(page):
                success += 1
            else:
                failed += 1

        return success, failed


async def main():
    """Run the crawler with CLI options"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Crawl Yale websites for RAG indexing")
    parser.add_argument(
        '--sites',
        nargs='+',
        choices=list(SEED_URLS.keys()),
        help='Specific sites to crawl (default: all)',
    )
    parser.add_argument(
        '--max-depth',
        type=int,
        default=2,
        help='Maximum crawl depth (default: 2)',
    )
    parser.add_argument(
        '--max-pages',
        type=int,
        default=50,
        help='Maximum pages per site (default: 50)',
    )
    parser.add_argument(
        '--output',
        type=str,
        default='crawled_pages.json',
        help='Output JSON file (default: crawled_pages.json)',
    )
    parser.add_argument(
        '--index',
        action='store_true',
        help='Send crawled pages to backend for indexing',
    )
    parser.add_argument(
        '--backend-url',
        type=str,
        default='http://localhost:8000',
        help='Backend API URL (default: http://localhost:8000)',
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=0.5,
        help='Delay between requests in seconds (default: 0.5)',
    )

    args = parser.parse_args()

    # Run crawler
    crawler = YaleCrawler(
        max_depth=args.max_depth,
        max_pages_per_site=args.max_pages,
        delay_between_requests=args.delay,
    )

    pages = await crawler.crawl_all(sites=args.sites)

    # Save to JSON
    output_data = [page.to_dict() for page in pages]
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)
    logger.info(f"\nSaved {len(pages)} pages to {args.output}")

    # Optionally index to backend
    if args.index:
        logger.info(f"\nIndexing pages to backend at {args.backend_url}...")
        indexer = BackendIndexer(args.backend_url)
        success, failed = await indexer.index_pages(pages)
        logger.info(f"Indexing complete: {success} succeeded, {failed} failed")


if __name__ == "__main__":
    asyncio.run(main())
