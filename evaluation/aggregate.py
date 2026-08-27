from __future__ import annotations

from collections import defaultdict


def by_context(rows: list[dict]) -> dict[int, list[dict]]:
    out: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        out[int(row["target_tokens"])].append(row)
    return dict(out)
