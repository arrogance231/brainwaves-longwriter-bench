from __future__ import annotations


def term_recall(text: str, terms: list[str]) -> float:
    if not terms:
        return 1.0
    lowered = text.casefold()
    return sum(term.casefold() in lowered for term in terms) / len(terms)


def forbidden_hits(text: str, terms: list[str]) -> list[str]:
    lowered = text.casefold()
    return [term for term in terms if term.casefold() in lowered]
