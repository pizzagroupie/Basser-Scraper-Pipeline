"""Telegram sender for review-first workflow."""
from __future__ import annotations

import html
import logging

import requests

import config
from models import ProcessedItem

logger = logging.getLogger(__name__)


def is_enabled() -> bool:
    return bool(config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID)


def send_review_item(item: ProcessedItem) -> bool:
    if not is_enabled():
        logger.warning("Telegram is not configured; skip send")
        return False

    message = _build_message(item)
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": message[:4096],
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code == 200:
            logger.info("Sent review item to Telegram: %s", item.source_title)
            return True
        logger.error("Telegram send failed: %s %s", resp.status_code, resp.text)
        return False
    except requests.RequestException as exc:
        logger.error("Telegram request error: %s", exc)
        return False


def send_summary(total_discovered: int, passed: int, sent: int, skipped: int) -> bool:
    if not is_enabled():
        return False

    text = (
        "<b>Bass Pipeline Summary</b>\n"
        f"Discovered: {total_discovered}\n"
        f"Passed strict filter: {passed}\n"
        f"Sent to review: {sent}\n"
        f"Skipped: {skipped}"
    )

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }

    try:
        resp = requests.post(url, json=payload, timeout=30)
        return resp.status_code == 200
    except requests.RequestException:
        return False


def _build_message(item: ProcessedItem) -> str:
    g = item.generation
    titles = "\n".join(f"- {html.escape(t)}" for t in g.xhs_titles)

    return (
        "<b>[REVIEW] Freshwater Largemouth Candidate</b>\n\n"
        f"<b>Source:</b> {html.escape(item.source)}\n"
        f"<b>Title:</b> {html.escape(item.source_title)}\n"
        f"<b>Published:</b> {html.escape(item.source_published_at or 'N/A')}\n"
        f"<b>URL:</b> {html.escape(item.source_url)}\n"
        f"<b>Filter:</b> {html.escape(item.filter_reason)}\n\n"
        "<b>CN Summary</b>\n"
        f"{html.escape(g.summary_cn)}\n\n"
        "<b>Xiaohongshu Titles</b>\n"
        f"{titles}\n\n"
        "<b>Xiaohongshu Caption</b>\n"
        f"{html.escape(g.xhs_caption)}\n"
        f"{html.escape(g.xhs_hashtags)}\n\n"
        "<b>Douyin Hook</b>\n"
        f"{html.escape(g.douyin_hook)}\n\n"
        "<b>Douyin Script</b>\n"
        f"{html.escape(g.douyin_script)}\n\n"
        "<b>Douyin CTA</b>\n"
        f"{html.escape(g.douyin_cta)}"
    )