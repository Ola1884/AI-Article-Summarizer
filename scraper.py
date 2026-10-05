import requests
import time
from bs4 import BeautifulSoup
from datetime import datetime
import os
from dotenv import load_dotenv
from error_log import log_error

load_dotenv()
API_KEY = os.getenv('SCRAPER_API_KEY')

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

HOMEPAGE_URLS = {
    "https://techcrunch.com",
    "https://www.techcrunch.com",
}


# ============================================================
# NETWORK LAYER (with retries + error logging)
# ============================================================
def _fetch_html(url, max_retries=3):
    """
    Fetches HTML via ScraperAPI with automatic retries and error logging.
    Returns the HTML string, or None on failure.
    """
    payload = {"api_key": API_KEY, "url": url}

    for attempt in range(max_retries):
        try:
            response = requests.get(
                "https://api.scraperapi.com",
                params=payload,
                headers=headers,
                timeout=60,
            )
            response.raise_for_status()
            return response.text

        except requests.exceptions.ConnectionError as e:
            log_error(
                context="scraper._fetch_html",
                error_type="connection",
                message=f"Attempt {attempt + 1}/{max_retries}: {e}",
                url=url,
            )
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

        except requests.exceptions.Timeout as e:
            log_error(
                context="scraper._fetch_html",
                error_type="connection",
                message=f"Attempt {attempt + 1}/{max_retries} timed out.",
                url=url,
            )
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

        except requests.exceptions.HTTPError:
            log_error(
                context="scraper._fetch_html",
                error_type="connection",
                message=f"HTTP {response.status_code} for {url}",
                url=url,
            )
            return None

        except requests.exceptions.RequestException as e:
            log_error(
                context="scraper._fetch_html",
                error_type="connection",
                message=f"Unhandled request error: {e}",
                url=url,
            )
            return None

    return None


# ============================================================
# CONTENT EXTRACTION
# ============================================================
def _extract_content_from_soup(soup):
    """Extracts article body text from an already-parsed BeautifulSoup object."""
    article_container = soup.find('div', class_='entry-content')

    if not article_container:
        log_error(
            context="scraper._extract_content_from_soup",
            error_type="html_structure",
            message="Could not find div.entry-content — TechCrunch HTML may have changed.",
        )
        return "N/A"

    all_paragraphs = article_container.find_all('p', class_="wp-block-paragraph")

    if not all_paragraphs:
        log_error(
            context="scraper._extract_content_from_soup",
            error_type="html_structure",
            message="No <p class='wp-block-paragraph'> tags found inside entry-content.",
        )
        return "N/A"

    cleaned_paragraphs = []
    for p in all_paragraphs:
        is_ad = any(
            cls in ('tc-event-inline-cta', 'hb-modal-container')
            for parent in p.parents
            for cls in (parent.get('class') or [])
        )
        if is_ad:
            continue

        text = p.get_text(strip=True)
        if text and len(text) > 30:
            cleaned_paragraphs.append(text)

    return "\n\n".join(cleaned_paragraphs) if cleaned_paragraphs else "N/A"


def _extract_article_metadata(soup):
    """Extracts Title, Author, Published Date from an article page."""
    # Title
    title = "Untitled"
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)

    # Author — with layered fallbacks
    author = "N/A"
    author_tag = soup.find("a", class_="post-authors-list__author")
    if not author_tag:
        author_tag = soup.find("a", href=lambda h: h and "/author/" in h)
    if not author_tag:
        author_tag = soup.find(attrs={"rel": "author"})

    if author_tag:
        author = author_tag.get_text(strip=True)
    else:
        log_error(
            context="scraper._extract_article_metadata",
            error_type="html_structure",
            message="Author selector returned nothing.",
        )

    # Published date
    published = "N/A"
    meta_group = soup.find("div", class_="wp-block-group article__meta")
    time_tag = meta_group.find("time") if meta_group else soup.find("time")
    if time_tag and time_tag.has_attr("datetime"):
        published = time_tag["datetime"]

    return title, author, published


# ============================================================
# SINGLE-ARTICLE FETCHER
# ============================================================
def get_article_content(url):
    """Fetches just the article body text."""
    html = _fetch_html(url)
    if html is None:
        return "N/A"
    soup = BeautifulSoup(html, "html.parser")
    return _extract_content_from_soup(soup)


# ============================================================
# HOMEPAGE SCRAPING
# ============================================================
def _scrape_homepage(num_articles, articles_url):
    html = _fetch_html(articles_url)
    if html is None:
        return []

    soup = BeautifulSoup(html, "html.parser")
    latest_section = soup.find('div', class_='latest-news-section')

    if not latest_section:
        log_error(
            context="scraper._scrape_homepage",
            error_type="html_structure",
            message="Could not find div.latest-news-section — homepage may have changed.",
            url=articles_url,
        )
        return []

    cards = latest_section.select('div.loop-card')

    if not cards:
        log_error(
            context="scraper._scrape_homepage",
            error_type="html_structure",
            message="No div.loop-card elements found inside latest-news-section.",
            url=articles_url,
        )
        return []

    metadata = []
    for card in cards:
        title_tag = card.select_one('a.loop-card__title-link')
        title = title_tag.get_text(strip=True) if title_tag else 'N/A'
        url = title_tag['href'] if title_tag and title_tag.has_attr('href') else 'N/A'

        author_tag = card.select_one('a.loop-card__author')
        author = author_tag.get_text(strip=True) if author_tag else 'N/A'

        time_tag = card.find('time', class_='loop-card__time')
        published_date = time_tag.get('datetime') if time_tag else "N/A"

        metadata.append({
            "Title": title,
            "URL": url,
            "Author": author,
            "Published Date": published_date,
            "Content": None,
        })

    valid = [a for a in metadata if a['Published Date'] != "N/A"]
    try:
        latest_n = sorted(
            valid,
            key=lambda x: datetime.fromisoformat(x['Published Date']),
            reverse=True,
        )[:num_articles]
    except ValueError:
        latest_n = valid[:num_articles]

    for article in latest_n:
        if article['URL'] != 'N/A':
            article['Content'] = get_article_content(article['URL'])
            time.sleep(1)
        else:
            article['Content'] = "N/A"

    return latest_n


# ============================================================
# PUBLIC ENTRY POINT
# ============================================================
def scrape_latest_articles(num_articles=3, articles_url="https://techcrunch.com/"):
    normalized = articles_url.rstrip("/")

    if normalized in HOMEPAGE_URLS:
        return _scrape_homepage(num_articles, articles_url)

    # Single-article mode
    html = _fetch_html(articles_url)
    if html is None:
        return []

    soup = BeautifulSoup(html, "html.parser")
    title, author, published = _extract_article_metadata(soup)
    content = _extract_content_from_soup(soup)

    if content == "N/A":
        return []

    return [{
        "Title": title,
        "URL": articles_url,
        "Author": author,
        "Published Date": published,
        "Content": content,
    }]


if __name__ == "__main__":
    articles = scrape_latest_articles(3)
    for a in articles:
        print(f"{a['Title']} — {a['Author']} ({a['Published Date']})")