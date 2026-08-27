#!/usr/bin/env python3
"""Deterministic machine checks; subjective prose scores remain external/blinded."""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


def ngram_repetition(text: str, n: int = 5) -> float:
    tokens = re.findall(r"\w+", text.lower())
    if len(tokens) < n:
        return 0.0
    grams = [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]
    return 1.0 - len(set(grams)) / len(grams)


def sentence_repeat(text: str) -> float:
    sentences = [re.sub(r"\s+", " ", x.strip().lower()) for x in re.split(r"[.!?]+", text) if x.strip()]
    if len(sentences) < 2:
        return 0.0
    return 1.0 - len(set(sentences)) / len(sentences)


def score_row(row: dict) -> dict:
    text = row.get("response", "")
    lower = text.lower()
    expected = row.get("expected_terms", [])
    forbidden = row.get("forbidden_terms", [])
    hits = {term: term.lower() in lower for term in expected}
    forbidden_hits = {term: term.lower() in lower for term in forbidden}
    continuity = sum(hits.values()) / len(hits) if hits else 1.0
    return {
        "expected_hits": hits,
        "expected_rate": continuity,
        "forbidden_hits": forbidden_hits,
        "knowledge_leakage": any(forbidden_hits.values()),
        "word_count": len(re.findall(r"\b\w+\b", text)),
        "exact_repetition_fraction": sentence_repeat(text),
        "ngram_repetition_fraction": ngram_repetition(text),
        "continuity_pass": continuity >= 0.9 and not any(forbidden_hits.values()),
    }


def label(stats: dict) -> str:
    if stats["failures"] or stats["continuity_rate"] < 0.5:
        return "FAILED"
    if stats["continuity_rate"] >= 0.9 and stats["knowledge_leakage"] == 0 and stats["manual_reviewed"]:
        return "PRODUCTION" if stats["manual_mean"] >= 4.0 else "USABLE"
    if stats["continuity_rate"] >= 0.75:
        return "DEGRADED"
    return "EXPERIMENTAL"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--markdown", required=True)
    args = ap.parse_args()
    rows = [json.loads(line) for line in Path(args.input).read_text().splitlines() if line.strip()]
    scored = []
    for row in rows:
        row["machine"] = score_row(row)
        scored.append(row)
    groups = defaultdict(list)
    for row in scored:
        groups[row["target_tokens"]].append(row)
    summaries = []
    for length, items in sorted(groups.items()):
        good = [x for x in items if x.get("ok") and x["machine"]["continuity_pass"]]
        failures = sum(not x.get("ok") for x in items)
        leaked = sum(x["machine"]["knowledge_leakage"] for x in items)
        continuity = sum(x["machine"]["continuity_pass"] for x in items) / len(items)
        summaries.append({"target_tokens": length, "cases": len(items), "failures": failures, "continuity_rate": continuity, "knowledge_leakage": leaked, "mean_ngram_repetition": sum(x["machine"]["ngram_repetition_fraction"] for x in items) / len(items), "manual_reviewed": False, "manual_mean": None})
    overall = {
        "cases": len(scored),
        "failures": sum(not x.get("ok") for x in scored),
        "continuity_rate": sum(x["machine"]["continuity_pass"] for x in scored) / len(scored) if scored else 0,
        "knowledge_leakage": sum(x["machine"]["knowledge_leakage"] for x in scored),
        "manual_reviewed": False,
        "manual_mean": None,
    }
    report = {"schema_version": "1.0", "input": args.input, "overall": overall, "by_context": summaries, "label": label(overall), "subjective_scores": "pending external/blinded review", "rows": scored}
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    md = ["# Arro LongWriter Bench result", "", f"Label: **{report['label']}** (manual prose review pending)", "", "| Context | Cases | Continuity | Leakage | Mean 5-gram repetition | Failures |", "|---:|---:|---:|---:|---:|---:|"]
    for item in summaries:
        md.append(f"| {item['target_tokens']:,} | {item['cases']} | {item['continuity_rate']:.3f} | {item['knowledge_leakage']} | {item['mean_ngram_repetition']:.4f} | {item['failures']} |")
    md += ["", "Machine checks are deterministic. Add blinded manual/judge scores for voice, dialogue, fluency, coherence, pacing, subtext, and callback naturalness before promotion.", ""]
    Path(args.markdown).write_text("\n".join(md))
    print(json.dumps({"label": report["label"], "overall": overall}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
