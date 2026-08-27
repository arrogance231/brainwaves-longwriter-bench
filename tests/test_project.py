from __future__ import annotations

import json
import unittest
from pathlib import Path

from benchmarks.arro_longwriter.fixtures.common import build_fixture
from benchmarks.arro_longwriter.score import score_row


class FixtureTests(unittest.TestCase):
    def test_nested_fixture_is_deterministic(self):
        a = build_fixture(8192, "single_needle", 101)
        b = build_fixture(8192, "single_needle", 101)
        self.assertEqual(a["fixture_id"], b["fixture_id"])
        self.assertEqual(a["prompt"], b["prompt"])

    def test_gold_state_schema(self):
        path = Path(__file__).parents[1] / "benchmarks/arro_longwriter/gold_state/events.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        self.assertGreaterEqual(len(rows), 10)
        self.assertTrue(all({"event_id", "token_region", "participants", "facts_created"} <= set(r) for r in rows))

    def test_scoring_continuity_and_leakage(self):
        row = {"response": "The blue kettle and red atlas matter; Natsumi never learned the paper crane.", "expected_terms": ["blue kettle", "red atlas"], "forbidden_terms": ["paper crane"]}
        score = score_row(row)
        self.assertEqual(score["expected_rate"], 1.0)
        self.assertTrue(score["knowledge_leakage"])


if __name__ == "__main__":
    unittest.main()
