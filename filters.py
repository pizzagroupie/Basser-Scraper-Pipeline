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
    "\u5927\u53e3\u9ed1\u9c88",
    "\u9ed1\u9c88",
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


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _find_hits(text: str, terms: list[str]) -> list[str]:
    hits: list[str] = []
    for term in terms:
        if term in text:
            hits.append(term)
    return hits


def evaluate_largemouth_only(title: str, text: str, url: str = "") -> FilterResult:
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
    if not species_hits:
        return FilterResult(
            passed=False,
            reason="no_largemouth_signal",
        )

    freshwater_hits = _find_hits(merged, FRESHWATER_TERMS)
    if not freshwater_hits:
        return FilterResult(
            passed=False,
            reason="no_freshwater_signal",
            species_hits=species_hits,
        )

    return FilterResult(
        passed=True,
        reason="passed_strict_largemouth_freshwater_filter",
        species_hits=species_hits,
        freshwater_hits=freshwater_hits,
    )