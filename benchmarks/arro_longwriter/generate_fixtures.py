#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from benchmarks.arro_longwriter.fixtures.common import SCENARIOS, build_fixture


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lengths", default="8192,16384,32768,65536,131072,196608,262144,393216,524288,768000,1010000")
    ap.add_argument("--scenarios", default="all")
    ap.add_argument("--seeds", default="101,202,303")
    ap.add_argument("--samples", type=int, default=1)
    ap.add_argument("--output", default="benchmarks/arro_longwriter/fixtures/manifest.jsonl")
    ap.add_argument("--include-prompt", action="store_true")
    ap.add_argument("--validate", action="store_true")
    args = ap.parse_args()
    lengths = [int(x) for x in args.lengths.split(",") if x]
    scenarios = list(SCENARIOS) if args.scenarios == "all" else [x for x in args.scenarios.split(",") if x]
    seeds = [int(x) for x in args.seeds.split(",") if x]
    rows = []
    for length in lengths:
        for seed in seeds:
            for scenario in scenarios:
                for sample in range(args.samples):
                    fixture = build_fixture(length, scenario, seed, sample)
                    if not args.include_prompt:
                        fixture.pop("prompt", None)
                    rows.append(fixture)
    if args.validate:
        assert rows, "no fixtures generated"
        assert len({r["fixture_id"] for r in rows}) == len(rows), "fixture IDs collide"
        assert all(r["story_chars"] >= r["target_tokens"] * 3 for r in rows)
        print(f"validated {len(rows)} deterministic fixtures")
        return 0
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    print(f"wrote {len(rows)} fixtures to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
