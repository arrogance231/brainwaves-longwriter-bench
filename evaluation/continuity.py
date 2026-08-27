from __future__ import annotations


def continuity(expected_terms: list[str], response: str, forbidden_terms: list[str] | None = None) -> dict:
    forbidden_terms = forbidden_terms or []
    lower = response.casefold()
    hits = {term: term.casefold() in lower for term in expected_terms}
    forbidden = {term: term.casefold() in lower for term in forbidden_terms}
    rate = sum(hits.values()) / len(hits) if hits else 1.0
    return {"hits": hits, "rate": rate, "forbidden": forbidden, "pass": rate >= 0.9 and not any(forbidden.values())}
