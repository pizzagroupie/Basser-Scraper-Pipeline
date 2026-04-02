# Basser Scraper Pipeline

Automated content pipeline for **freshwater largemouth bass only**.

It scans selected JP/US bass sources, filters strictly for `largemouth bass + freshwater context`, generates Chinese social copy, then sends review-ready drafts to Telegram. Optional Notion sync is supported.

## Sources (V1)

- Basser: `https://web.tsuribito.co.jp/basser`
- JB-NBC: `https://www.jbnbc.jp/_JB2026/`
- WBS: `https://www.wbs1.jp/`
- LureNewsR: `https://www.lurenewsr.com/feed/`
- MLF: `https://majorleaguefishing.com/feed/`
- Bassmaster: `https://www.bassmaster.com/news/feed/`

## Strict Filter Rules

The pipeline keeps an item only if:

1. It contains a largemouth species signal:
   - `largemouth bass`
   - `Micropterus salmoides`
   - `\u30e9\u30fc\u30b8\u30de\u30a6\u30b9\u30d0\u30b9`
   - `\u30aa\u30aa\u30af\u30c1\u30d0\u30b9`

2. It contains freshwater context signal:
   - `freshwater`, `lake`, `reservoir`, `river`, `dam`, etc.

3. For trusted black-bass tournament sources, `species signal + trusted source` can pass even if freshwater words are omitted in the title/body.

4. It does **not** contain excluded species/context:
   - `smallmouth bass`, `spotted bass`, `striped bass`, `sea bass`, `seabass`, etc.
   - `bass guitar`

## Output

For each passed article:

- Chinese faithful summary
- Xiaohongshu package:
  - 3 title options
  - caption
  - hashtag line
- Douyin package:
  - hook
  - 30-60s style script text
  - CTA line

## Required GitHub Secrets

Add these in `Settings -> Secrets and variables -> Actions`:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `OPENAI_API_KEY`

Optional:

- `OPENAI_BASE_URL` (if using an OpenAI-compatible endpoint)
- `OPENAI_MODEL` (default: `gpt-5-mini`)
- `NOTION_TOKEN`
- `NOTION_DATABASE_ID`

## Quick Start

1. Push this folder to a new GitHub repo.
2. Add required secrets.
3. Open `Actions` tab, enable workflows.
4. Run `Basser Pipeline` once with `Run workflow`.
5. Check your Telegram chat for review messages.

## Optional Notion Sync

If `NOTION_TOKEN` and `NOTION_DATABASE_ID` are set, each passed item is written to Notion.

Expected property names in your Notion database:

- `Item ID` (Title)
- `Status` (Select)
- `Source` (Select)
- `Source URL` (URL)
- `Published At (Source)` (Date)
- `Fetched At` (Date)
- `Raw Excerpt` (Text)
- `CN Summary` (Text)
- `XHS Title A` (Text)
- `XHS Title B` (Text)
- `XHS Title C` (Text)
- `XHS Caption` (Text)
- `XHS Hashtags` (Text)
- `Douyin Hook` (Text)
- `Douyin Script` (Text)
- `Douyin CTA` (Text)
- `Compliance Note` (Text)

## Runtime Settings

You can tune these environment variables if needed:

- `MAX_ITEMS_PER_RUN` (default `8`)
- `DISCOVERY_LIMIT_PER_SOURCE` (default `30`)
- `REQUEST_DELAY_SECONDS` (default `1.2`)
- `REQUEST_TIMEOUT_SECONDS` (default `30`)

## Notes

- Deduplication state is stored in `data/seen_items.json`.
- Workflow auto-commits this file after each run.
- If Telegram is down in a run, passed items are not marked as seen so they can retry next run.
