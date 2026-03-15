"""Main orchestrator for freshwater largemouth bass content pipeline."""
from __future__ import annotations

import hashlib
import logging
import sys

import config
import notion_client
import telegram_sender
from ai_writer import generate_social_copy
from filters import evaluate_largemouth_only
from models import Article, FilterResult, ProcessedItem
from scraper import discover_entries, fetch_article
from source_registry import SOURCES
from storage import SeenStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("=" * 70)
    logger.info("Basser Scraper Pipeline started")
    logger.info("Strict policy: freshwater + largemouth bass only")
    logger.info("=" * 70)

    seen_store = SeenStore()
    seen_store.load()

    discovered_count = 0
    passed_count = 0
    sent_count = 0
    skipped_count = 0

    for source in SOURCES:
        if sent_count >= config.MAX_ITEMS_PER_RUN:
            break

        logger.info("Scanning source: %s", source.name)
        try:
            entries = discover_entries(source, config.DISCOVERY_LIMIT_PER_SOURCE)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Source discovery failed (%s): %s", source.name, exc)
            continue

        discovered_count += len(entries)
        logger.info("Discovered %s candidates from %s", len(entries), source.name)

        for entry in entries:
            if sent_count >= config.MAX_ITEMS_PER_RUN:
                break

            item_id = _make_item_id(entry.source, entry.url)
            if seen_store.has(item_id):
                skipped_count += 1
                continue

            try:
                article = fetch_article(entry.url, fallback_title=entry.title)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Article fetch failed, fallback to RSS summary: %s (%s)", entry.url, exc)
                if not entry.summary.strip():
                    continue
                article = Article(
                    url=entry.url,
                    title=entry.title,
                    text=entry.summary,
                    published_at=entry.published_at,
                )

            content_title = article.title or entry.title
            filter_result = evaluate_largemouth_only(
                title=content_title,
                text=article.text,
                url=entry.url,
                source=entry.source,
            )

            if not filter_result.passed:
                logger.info(
                    "Filtered out: %s | reason=%s",
                    content_title,
                    filter_result.reason,
                )
                skipped_count += 1
                seen_store.add(item_id)
                continue

            passed_count += 1
            generation = generate_social_copy(
                source=entry.source,
                title=content_title,
                url=entry.url,
                article_text=article.text,
            )

            filter_label = _build_filter_label(filter_result)
            processed = ProcessedItem(
                item_id=item_id,
                source=entry.source,
                source_url=entry.url,
                source_title=content_title,
                source_published_at=entry.published_at or article.published_at,
                raw_excerpt=_clip(article.text, 500),
                filter_reason=filter_label,
                generation=generation,
            )

            if notion_client.is_enabled():
                notion_client.create_page(processed)

            sent_ok = telegram_sender.send_review_item(processed)
            if sent_ok:
                sent_count += 1
                seen_store.add(item_id)
            else:
                logger.warning("Telegram send failed; will retry in next run: %s", entry.url)

    seen_store.save()
    telegram_sender.send_summary(
        total_discovered=discovered_count,
        passed=passed_count,
        sent=sent_count,
        skipped=skipped_count,
    )

    logger.info("Run completed. discovered=%s passed=%s sent=%s skipped=%s", discovered_count, passed_count, sent_count, skipped_count)


def _make_item_id(source: str, url: str) -> str:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    source_key = source.lower().replace(" ", "-")
    return f"{config.FILTER_VERSION}-{source_key}-{digest}"


def _clip(text: str, max_len: int) -> str:
    clean = " ".join(text.split())
    if len(clean) <= max_len:
        return clean
    return clean[:max_len].rstrip() + "..."


def _build_filter_label(result: FilterResult) -> str:
    parts = [result.reason]
    if result.species_hits:
        parts.append("species=" + ",".join(result.species_hits[:3]))
    if result.freshwater_hits:
        parts.append("freshwater=" + ",".join(result.freshwater_hits[:3]))
    return " | ".join(parts)


if __name__ == "__main__":
    main()
