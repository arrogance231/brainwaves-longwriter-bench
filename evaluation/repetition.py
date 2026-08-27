from __future__ import annotations

import re


def ngram_fraction(text: str, n: int = 5) -> float:
    tokens = re.findall(r"\w+", text.lower())
    if len(tokens) < n:
        return 0.0
    grams = [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]
    return 1.0 - len(set(grams)) / len(grams)


def sentence_fraction(text: str) -> float:
    items = [re.sub(r"\s+", " ", s.strip().lower()) for s in re.split(r"[.!?]+", text) if s.strip()]
    return 0.0 if len(items) < 2 else 1.0 - len(set(items)) / len(items)
