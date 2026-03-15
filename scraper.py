"""Content discovery and article extraction."""
from __future__ import annotations

import re
import time
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

import config
from models import Article, RawEntry, SourceDefinition


SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": config.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
)

LINK_HINTS = ["news", "article", "blog", "report", "entry", "column", "bass", "tournament"]
SKIP_TITLE_WORDS = [
    "privacy",
    "policy",
    "contact",
    "about",
    "login",
    "register",
    "cookie",
    "terms",
]


def discover_entries(source: SourceDefinition, limit: int) -> list[RawEntry]:
    if source.parser == "rss":
        entries = _discover_from_rss(source, limit)
    else:
        entries = _discover_from_html(source, limit)

    time.sleep(config.REQUEST_DELAY_SECONDS)
    return entries


def _discover_from_rss(source: SourceDefinition, limit: int) -> list[RawEntry]:
    feed = feedparser.parse(source.entry_url)
    items: list[RawEntry] = []
    seen_urls: set[str] = set()

    for entry in feed.entries:
        url = entry.get("link", "").strip()
        title = entry.get("title", "").strip()
        if not url or not title:
            continue

        canonical_url = _canonical_url(url)
        if canonical_url in seen_urls:
            continue
        seen_urls.add(canonical_url)

        published = (
            entry.get("published", "")
            or entry.get("updated", "")
            or entry.get("created", "")
        )
        items.append(
            RawEntry(
                source=source.name,
                url=canonical_url,
                title=title,
                published_at=published,
            )
        )
        if len(items) >= limit:
            break

    return items


def _discover_from_html(source: SourceDefinition, limit: int) -> list[RawEntry]:
    response = SESSION.get(source.entry_url, timeout=config.REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    base_host = urlparse(source.base_url).netloc

    scored: list[tuple[int, RawEntry]] = []
    seen_urls: set[str] = set()

    for tag in soup.find_all("a", href=True):
        raw_href = tag.get("href", "").strip()
        title = " ".join(tag.get_text(" ", strip=True).split())
        if len(title) < 12:
            continue

        url = _canonical_url(urljoin(source.base_url, raw_href))
        if not url.startswith("http"):
            continue
        if urlparse(url).netloc != base_host:
            continue
        if any(word in title.lower() for word in SKIP_TITLE_WORDS):
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)

        score = 0
        lowered_path = urlparse(url).path.lower()
        score += sum(1 for hint in LINK_HINTS if hint in lowered_path)
        if re.search(r"/20\d{2}/", lowered_path):
            score += 2
        if len(title) > 24:
            score += 1

        scored.append(
            (
                score,
                RawEntry(
                    source=source.name,
                    url=url,
                    title=title,
                    published_at="",
                ),
            )
        )

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored[:limit]]


def fetch_article(url: str, fallback_title: str = "") -> Article:
    response = SESSION.get(url, timeout=config.REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for bad in soup.select("script,style,noscript,nav,footer,header,aside,form"):
        bad.decompose()

    title = (
        _meta_content(soup, "property", "og:title")
        or _meta_content(soup, "name", "twitter:title")
        or (soup.title.get_text(strip=True) if soup.title else "")
        or fallback_title
    )

    published = (
        _meta_content(soup, "property", "article:published_time")
        or _meta_content(soup, "name", "pubdate")
        or _meta_content(soup, "name", "date")
    )

    root = soup.find("article") or soup.find("main") or soup.body or soup
    paragraphs: list[str] = []
    for p in root.find_all("p"):
        text = " ".join(p.get_text(" ", strip=True).split())
        if len(text) < 40:
            continue
        paragraphs.append(text)
        if len(paragraphs) >= config.MAX_PARAGRAPHS_PER_ARTICLE:
            break

    if not paragraphs:
        body_text = " ".join(root.get_text(" ", strip=True).split())
        chunks = re.split(r"(?<=[.!?])\s+", body_text)
        for chunk in chunks:
            if len(chunk) >= 40:
                paragraphs.append(chunk)
            if len(paragraphs) >= config.MAX_PARAGRAPHS_PER_ARTICLE:
                break

    text = "\n\n".join(paragraphs)
    if len(text) > config.MAX_CHARS_PER_ARTICLE:
        text = text[: config.MAX_CHARS_PER_ARTICLE]

    time.sleep(config.REQUEST_DELAY_SECONDS)
    return Article(url=url, title=title, text=text, published_at=published)


def _meta_content(soup: BeautifulSoup, key: str, value: str) -> str:
    tag = soup.find("meta", attrs={key: value})
    if not tag:
        return ""
    return (tag.get("content") or "").strip()


def _canonical_url(url: str) -> str:
    parsed = urlparse(url)
    clean_path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme}://{parsed.netloc}{clean_path}"