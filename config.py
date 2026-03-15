"""Runtime configuration for the bass content pipeline."""
from __future__ import annotations

import os

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# --- OpenAI-compatible text generation ---
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
OPENAI_MODEL = os.environ.get("OPENAI_MODEL") or "gpt-5-mini"
OPENAI_TIMEOUT_SECONDS = int(os.environ.get("OPENAI_TIMEOUT_SECONDS", "60"))

# --- Notion (optional) ---
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "")
NOTION_VERSION = "2022-06-28"

# --- Crawl behavior ---
REQUEST_TIMEOUT_SECONDS = int(os.environ.get("REQUEST_TIMEOUT_SECONDS", "30"))
REQUEST_DELAY_SECONDS = float(os.environ.get("REQUEST_DELAY_SECONDS", "1.2"))
DISCOVERY_LIMIT_PER_SOURCE = int(os.environ.get("DISCOVERY_LIMIT_PER_SOURCE", "30"))
MAX_ITEMS_PER_RUN = int(os.environ.get("MAX_ITEMS_PER_RUN", "8"))
MAX_PARAGRAPHS_PER_ARTICLE = int(os.environ.get("MAX_PARAGRAPHS_PER_ARTICLE", "40"))
MAX_CHARS_PER_ARTICLE = int(os.environ.get("MAX_CHARS_PER_ARTICLE", "10000"))

USER_AGENT = os.environ.get(
    "USER_AGENT",
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/132.0.0.0 Safari/537.36"
    ),
)

# --- Data files ---
SEEN_ITEMS_FILE = os.environ.get("SEEN_ITEMS_FILE", "data/seen_items.json")

# --- Filtering policy ---
STRICT_LARGEMOUTH_ONLY = True
FILTER_VERSION = os.environ.get("FILTER_VERSION") or "v2"
