"""Dataclasses used across the pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SourceDefinition:
    name: str
    base_url: str
    entry_url: str
    parser: str  # rss | html
    language: str


@dataclass(slots=True)
class RawEntry:
    source: str
    url: str
    title: str
    published_at: str = ""
    summary: str = ""


@dataclass(slots=True)
class Article:
    url: str
    title: str
    text: str
    published_at: str = ""


@dataclass(slots=True)
class FilterResult:
    passed: bool
    reason: str
    species_hits: list[str] = field(default_factory=list)
    freshwater_hits: list[str] = field(default_factory=list)
    excluded_hits: list[str] = field(default_factory=list)


@dataclass(slots=True)
class GenerationResult:
    summary_cn: str
    xhs_titles: list[str]
    xhs_caption: str
    xhs_hashtags: str
    douyin_hook: str
    douyin_script: str
    douyin_cta: str


@dataclass(slots=True)
class ProcessedItem:
    item_id: str
    source: str
    source_url: str
    source_title: str
    source_published_at: str
    raw_excerpt: str
    filter_reason: str
    generation: GenerationResult
