from __future__ import annotations

from typing import Any, TypedDict


class RunRow(TypedDict, total=False):
    fixture_id: str
    target_tokens: int
    scenario: str
    seed: int
    response: str
    ok: bool
    usage: dict[str, Any]
    elapsed_s: float
    ttft_s: float | None
    machine: dict[str, Any]


REQUIRED_RESULT_KEYS = {"fixture_id", "target_tokens", "scenario", "seed", "ok", "response"}
