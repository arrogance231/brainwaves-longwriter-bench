#!/usr/bin/env python3
"""Generate dependency-free SVG plots from captured JSON."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def load_rows(path: str | None, key: str = "by_context") -> list[dict]:
    if not path or not Path(path).exists():
        return []
    data = json.loads(Path(path).read_text())
    return data.get(key, data.get("rows", []))


def svg_plot(path: Path, title: str, ylabel: str, points: list[tuple[int, float]], note: str = "") -> None:
    width, height = 760, 440
    left, right, top, bottom = 78, 28, 56, 72
    plot_w, plot_h = width - left - right, height - top - bottom
    if points:
        xs = [p[0] for p in points]; ys = [p[1] for p in points]
        xmin, xmax = min(xs), max(xs); ymin, ymax = min(ys), max(ys)
        if ymin == ymax: ymin, ymax = ymin - 1, ymax + 1
        pad = (ymax - ymin) * 0.08; ymin -= pad; ymax += pad
        def xpx(x: int) -> float:
            span = math.log10(max(xmax, 1)) - math.log10(max(xmin, 1))
            return left + (math.log10(max(x, 1)) - math.log10(max(xmin, 1))) / max(span, 1e-9) * plot_w
        def ypx(y: float) -> float: return top + (ymax - y) / (ymax - ymin) * plot_h
        poly = " ".join(f"{xpx(x):.1f},{ypx(y):.1f}" for x, y in points)
        marks = "".join(f'<circle cx="{xpx(x):.1f}" cy="{ypx(y):.1f}" r="4" fill="#2c7fb8"/><text x="{xpx(x):.1f}" y="{height-bottom+22}" text-anchor="middle" font-size="11">{x:,}</text>' for x, y in points)
        series = f'<polyline points="{poly}" fill="none" stroke="#2c7fb8" stroke-width="3"/>{marks}'
        subtitle = note
    else:
        series = f'<text x="{left+plot_w/2:.0f}" y="{top+plot_h/2:.0f}" text-anchor="middle" font-size="16" fill="#666">No measured data</text>'
        subtitle = note or "This metric is intentionally pending a blinded/quality-qualified run."
    body = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="white"/><text x="{width/2:.0f}" y="28" text-anchor="middle" font-size="20" font-family="sans-serif">{title}</text>
<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" stroke="#333"/><line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" stroke="#333"/>
{series}<text x="{width/2:.0f}" y="{height-18}" text-anchor="middle" font-size="13" font-family="sans-serif">context tokens (log scale)</text>
<text x="18" y="{top+plot_h/2:.0f}" transform="rotate(-90 18 {top+plot_h/2:.0f})" text-anchor="middle" font-size="13" font-family="sans-serif">{ylabel}</text>
<text x="{left}" y="{height-42}" font-size="11" fill="#555" font-family="sans-serif">{subtitle}</text></svg>'''
    path.write_text(body)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quality", default="results/aggregate/native-quality-v2.json")
    ap.add_argument("--throughput", default="results/aggregate/native-bf16-throughput-corrected.json")
    ap.add_argument("--output-dir", default="results/figures")
    args = ap.parse_args()
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    qrows = load_rows(args.quality)
    trows = load_rows(args.throughput, "rows")
    def qpoints(field: str) -> list[tuple[int, float]]:
        return [(int(r["target_tokens"]), float(r[field])) for r in qrows if r.get(field) is not None]
    def tpoints(field: str) -> list[tuple[int, float]]:
        return [(int(r["context_target_tokens"]), float(r[field])) for r in trows if r.get(field) is not None]
    plots = {
        "retrieval_accuracy_vs_context.svg": ("Retrieval accuracy vs context length", "accuracy", qpoints("continuity_rate")),
        "story_continuity_vs_context.svg": ("Story continuity vs context length", "continuity rate", qpoints("continuity_rate")),
        "prose_score_vs_context.svg": ("Prose score vs context length", "blinded score", []),
        "ttft_vs_context.svg": ("TTFT vs context length", "seconds", tpoints("ttft_s")),
        "prefill_tok_s_vs_context.svg": ("Prefill throughput vs context length", "tokens/sec", tpoints("prefill_tok_s")),
        "decode_tok_s_vs_context.svg": ("Decode throughput vs context length", "tokens/sec", tpoints("decode_tok_s")),
        "repetition_vs_context.svg": ("5-gram repetition vs context length", "fraction", qpoints("mean_ngram_repetition")),
    }
    # 16 full-attention layers * 4 KV heads * 256 dim * K/V * 2 bytes,
    # plus the verified 51.75 GiB BF16 weight file.
    memory = [(n, n * 16 * 4 * 256 * 2 * 2 / 2**30 + 51.75) for n in (262144, 524288, 1010000)]
    plots["hbm_vs_context.svg"] = ("Estimated weight + BF16 KV memory", "GiB", memory)
    for filename, (title, ylabel, points) in plots.items():
        svg_plot(out / filename, title, ylabel, points, "Source: captured aggregate JSON; missing subjective metrics are not imputed.")
    print(f"wrote {len(plots)} SVG plots to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
