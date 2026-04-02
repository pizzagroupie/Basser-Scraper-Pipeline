"""Source registry for the bass content pipeline."""
from __future__ import annotations

from models import SourceDefinition


SOURCES: list[SourceDefinition] = [
    SourceDefinition(
        name="Basser",
        base_url="https://web.tsuribito.co.jp",
        entry_url="https://web.tsuribito.co.jp/basser",
        parser="html",
        language="ja",
    ),
    SourceDefinition(
        name="JB-NBC",
        base_url="https://www.jbnbc.jp",
        entry_url="https://www.jbnbc.jp/_JB2026/",
        parser="html",
        language="ja",
    ),
    SourceDefinition(
        name="WBS",
        base_url="https://www.wbs1.jp",
        entry_url="https://www.wbs1.jp/",
        parser="html",
        language="ja",
    ),
    SourceDefinition(
        name="LureNewsR",
        base_url="https://www.lurenewsr.com",
        entry_url="https://www.lurenewsr.com/feed/",
        parser="rss",
        language="ja",
    ),
    SourceDefinition(
        name="MLF",
        base_url="https://majorleaguefishing.com",
        entry_url="https://majorleaguefishing.com/feed/",
        parser="rss",
        language="en",
    ),
    SourceDefinition(
        name="Bassmaster",
        base_url="https://www.bassmaster.com",
        entry_url="https://www.bassmaster.com/news/feed/",
        parser="rss",
        language="en",
    ),
]
