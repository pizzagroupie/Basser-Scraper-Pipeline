"""Optional Notion integration for content inventory."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import requests
from dateutil import parser as dateparser

import config
from models import ProcessedItem

logger = logging.getLogger(__name__)


def is_enabled() -> bool:
    return bool(config.NOTION_TOKEN and config.NOTION_DATABASE_ID)


def create_page(item: ProcessedItem) -> bool:
    if not is_enabled():
        return False

    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {config.NOTION_TOKEN}",
        "Notion-Version": config.NOTION_VERSION,
        "Content-Type": "application/json",
    }

    g = item.generation
    now = datetime.now(timezone.utc).isoformat()
    published_at = _safe_iso_datetime(item.source_published_at, fallback=now)

    payload = {
        "parent": {"database_id": config.NOTION_DATABASE_ID},
        "properties": {
            "Item ID": {"title": [_text_obj(item.item_id)]},
            "Status": {"select": {"name": "REVIEW"}},
            "Source": {"select": {"name": item.source}},
            "Source URL": {"url": item.source_url},
            "Published At (Source)": {"date": {"start": published_at}},
            "Fetched At": {"date": {"start": now}},
            "Raw Excerpt": {"rich_text": [_text_obj(item.raw_excerpt)]},
            "CN Summary": {"rich_text": [_text_obj(g.summary_cn)]},
            "XHS Title A": {"rich_text": [_text_obj(_pick(g.xhs_titles, 0))]},
            "XHS Title B": {"rich_text": [_text_obj(_pick(g.xhs_titles, 1))]},
            "XHS Title C": {"rich_text": [_text_obj(_pick(g.xhs_titles, 2))]},
            "XHS Caption": {"rich_text": [_text_obj(g.xhs_caption)]},
            "XHS Hashtags": {"rich_text": [_text_obj(g.xhs_hashtags)]},
            "Douyin Hook": {"rich_text": [_text_obj(g.douyin_hook)]},
            "Douyin Script": {"rich_text": [_text_obj(g.douyin_script)]},
            "Douyin CTA": {"rich_text": [_text_obj(g.douyin_cta)]},
            "Compliance Note": {"rich_text": [_text_obj(item.filter_reason)]},
        },
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code in (200, 201):
            logger.info("Notion page created: %s", item.item_id)
            return True
        logger.warning("Notion create failed: %s %s", resp.status_code, resp.text)
        return False
    except requests.RequestException as exc:
        logger.warning("Notion request error: %s", exc)
        return False


def _text_obj(text: str) -> dict:
    # Notion rich_text has per-node limits, keep each field compact.
    clipped = (text or "")[:1800]
    return {"type": "text", "text": {"content": clipped}}


def _pick(values: list[str], idx: int) -> str:
    if idx < len(values):
        return values[idx]
    return ""


def _safe_iso_datetime(value: str, fallback: str) -> str:
    if not value:
        return fallback
    try:
        parsed = dateparser.parse(value)
        if not parsed:
            return fallback
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    except Exception:  # noqa: BLE001
        return fallback
