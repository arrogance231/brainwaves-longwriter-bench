from __future__ import annotations

import re


def surface_metrics(text: str) -> dict:
    words = re.findall(r"\b\w+\b", text)
    sentences = [x for x in re.split(r"[.!?]+", text) if x.strip()]
    lengths = [len(re.findall(r"\b\w+\b", x)) for x in sentences]
    return {"word_count": len(words), "sentence_count": len(sentences), "mean_sentence_words": sum(lengths) / len(lengths) if lengths else 0.0, "question_rate": text.count("?") / max(1, len(sentences))}
