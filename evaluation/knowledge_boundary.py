from __future__ import annotations


def leakage(response: str, forbidden_facts: list[str]) -> dict:
    lower = response.casefold()
    hits = {fact: fact.casefold() in lower for fact in forbidden_facts}
    return {"hits": hits, "leakage": any(hits.values())}
