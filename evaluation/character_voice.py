from __future__ import annotations


def lexical_presence(text: str, fingerprint: dict[str, list[str]]) -> dict[str, float]:
    lower = text.casefold()
    return {name: sum(term.casefold() in lower for term in data.get("lexical", [])) / max(1, len(data.get("lexical", []))) for name, data in fingerprint.items()}
