"""Strict filtering for freshwater largemouth bass content only."""
from __future__ import annotations

from models import FilterResult

SPECIES_TERMS = [
    "largemouth bass",
    "micropterus salmoides",
    "large-mouth bass",
    "laegemouth",  # common typo in scraped text
    "\u30e9\u30fc\u30b8\u30de\u30a6\u30b9\u30d0\u30b9",  # Japanese
    "\u30aa\u30aa\u30af\u30c1\u30d0\u30b9",
    "\u30d6\u30e9\u30c3\u30af\u30d0\u30b9",
    "black bass",
    "largemouth",
    "\u5927\u53e3\u9ed1\u9c88",
    "\u9ed1\u9c88",
]

BASS_CONTEXT_TERMS = [
    "bass fishing",
    "\u30d0\u30b9\u30d5\u30a3\u30c3\u30b7\u30f3\u30b0",
    "\u30d0\u30b9\u91e3\u308a",
    "\u30c7\u30ab\u30d0\u30b9",
    "\u30aa\u30ab\u30c3\u30d1\u30ea",
    "\u30ea\u30b6\u30fc\u30d0\u30fc",
    "\u30d0\u30b9\u30dc\u30fc\u30c8",
]

FRESHWATER_TERMS = [
    "freshwater",
    "lake",
    "reservoir",
    "river",
    "inland water",
    "dam",
    "pond",
    "\u6de1\u6c34",
    "\u6e56",
    "\u6cb3\u5ddd",
    "\u30c0\u30e0",
    "\u6e56\u6cca",
]

EXCLUDED_TERMS = [
    "smallmouth bass",
    "spotted bass",
    "striped bass",
    "white bass",
    "sea bass",
    "seabass",
    "peacock bass",
    "barramundi",
    "lates calcarifer",
    "\u30b7\u30fc\u30d0\u30b9",
    "bass guitar",
]

TRUSTED_BLACK_BASS_SOURCES = {"Basser", "JB-NBC", "WBS", "MLF", "Bassmaster"}


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _find_hits(text: str, terms: list[str]) -> list[str]:
    hits: list[str] = []
    for term in terms:
        if term in text:
            hits.append(term)
    return hits


def evaluate_largemouth_only(title: str, text: str, url: str = "", source: str = "") -> FilterResult:
    """Allow only freshwater largemouth bass topics."""
    merged = _normalize(f"{title} {text} {url}")

    excluded_hits = _find_hits(merged, EXCLUDED_TERMS)
    if excluded_hits:
        return FilterResult(
            passed=False,
            reason="excluded_species_or_context",
            excluded_hits=excluded_hits,
        )

    species_hits = _find_hits(merged, SPECIES_TERMS)
    context_hits = _find_hits(merged, BASS_CONTEXT_TERMS)
    freshwater_hits = _find_hits(merged, FRESHWATER_TERMS)
    # Source-aware fallback:
    # Dedicated black-bass sources often omit explicit "largemouth" wording in titles.
    has_source_hint = source in TRUSTED_BLACK_BASS_SOURCES

    if species_hits and freshwater_hits:
        return FilterResult(
            passed=True,
            reason="passed_species_plus_freshwater",
            species_hits=species_hits,
            freshwater_hits=freshwater_hits,
        )

    if species_hits and has_source_hint:
        return FilterResult(
            passed=True,
            reason="passed_species_plus_trusted_source",
            species_hits=species_hits,
        )

    if not species_hits and not context_hits:
        return FilterResult(
            passed=False,
            reason="no_largemouth_or_black_bass_signal",
        )

    return FilterResult(
        passed=False,
        reason="no_freshwater_signal",
        species_hits=species_hits or context_hits,
    )
