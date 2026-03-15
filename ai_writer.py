"""Generate CN summaries and social copy from source articles."""
from __future__ import annotations

import json
import logging
import re

import requests

import config
from models import GenerationResult

logger = logging.getLogger(__name__)


def generate_social_copy(source: str, title: str, url: str, article_text: str) -> GenerationResult:
    if not config.OPENAI_API_KEY:
        return _fallback_generation(title=title, source=source, text=article_text)

    payload = {
        "model": config.OPENAI_MODEL,
        "temperature": 0.7,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a Chinese social media copywriter for bass fishing. "
                    "Only use the source for paraphrased summary. "
                    "Never copy long original text. "
                    "Output JSON only."
                ),
            },
            {
                "role": "user",
                "content": _build_user_prompt(source=source, title=title, url=url, text=article_text),
            },
        ],
    }

    endpoint = f"{config.OPENAI_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=config.OPENAI_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        raw_content = response.json()["choices"][0]["message"]["content"]
        parsed = _parse_json_block(raw_content)
        return _to_generation_result(parsed)
    except Exception as exc:  # noqa: BLE001
        logger.warning("OpenAI generation failed, using fallback: %s", exc)
        return _fallback_generation(title=title, source=source, text=article_text)


def _build_user_prompt(source: str, title: str, url: str, text: str) -> str:
    clipped = text[:5000]
    return (
        "Source: {source}\n"
        "Title: {title}\n"
        "URL: {url}\n\n"
        "Article:\n{article}\n\n"
        "Task:\n"
        "1) Write a faithful Chinese summary in <= 180 Chinese chars.\n"
        "2) Generate 3 Xiaohongshu title options (<= 20 chars each).\n"
        "3) Generate Xiaohongshu body (120-220 chars) and hashtags line with 6-10 tags.\n"
        "4) Generate Douyin hook (<= 20 chars), script (150-260 chars), CTA (<= 30 chars).\n"
        "5) Keep style practical and fishing-focused, avoid exaggerated claims.\n"
        "6) Return JSON exactly with keys:\n"
        "summary_cn, xhs_titles, xhs_caption, xhs_hashtags, douyin_hook, douyin_script, douyin_cta"
    ).format(source=source, title=title, url=url, article=clipped)


def _parse_json_block(content: str) -> dict:
    text = content.strip()
    code_block_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if code_block_match:
        text = code_block_match.group(1)
    return json.loads(text)


def _to_generation_result(data: dict) -> GenerationResult:
    titles = data.get("xhs_titles", [])
    if isinstance(titles, str):
        titles = [titles]
    titles = [str(t).strip() for t in titles if str(t).strip()][:3]

    return GenerationResult(
        summary_cn=str(data.get("summary_cn", "")).strip(),
        xhs_titles=titles,
        xhs_caption=str(data.get("xhs_caption", "")).strip(),
        xhs_hashtags=str(data.get("xhs_hashtags", "")).strip(),
        douyin_hook=str(data.get("douyin_hook", "")).strip(),
        douyin_script=str(data.get("douyin_script", "")).strip(),
        douyin_cta=str(data.get("douyin_cta", "")).strip(),
    )


def _fallback_generation(title: str, source: str, text: str) -> GenerationResult:
    short = _clip_text(text, 220)
    summary = f"[{source}] {title}. Key points: {short}"

    caption = (
        f"This article from {source} focuses on freshwater largemouth bass tactics. "
        f"Quick notes: {_clip_text(text, 120)} "
        "Use this as a reference and adjust by local water conditions."
    )

    script = (
        "Today we summarize one largemouth bass update. "
        f"Source: {source}. Core info: {_clip_text(text, 180)} "
        "Adapt by temperature, water color, and baitfish activity in your lake."
    )

    return GenerationResult(
        summary_cn=summary,
        xhs_titles=[
            "Freshwater largemouth notes",
            "One practical bass takeaway",
            "Overseas bass content digest",
        ],
        xhs_caption=caption,
        xhs_hashtags="#LargemouthBass #BassFishing #Freshwater #FishingTips #Xiaohongshu",
        douyin_hook="One bass tip in 30 sec",
        douyin_script=script,
        douyin_cta="What lure worked best for you this week?",
    )


def _clip_text(text: str, size: int) -> str:
    compact = " ".join(text.split())
    if len(compact) <= size:
        return compact
    return compact[:size].rstrip() + "..."