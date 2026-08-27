#!/usr/bin/env python3
"""Deterministic nested fixtures for Arro LongWriter Bench."""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = ROOT / "gold_state/events.jsonl"


def events() -> list[dict]:
    return [json.loads(line) for line in EVENTS_PATH.read_text().splitlines() if line.strip()]


SCENARIOS = {
    "single_needle": {"question": "Where did Minami say he would hate going on a date, and who learned that?", "terms": ["surprise amusement-park", "Arro"], "forbidden": ["Natsumi learned"]},
    "multi_needle": {"question": "Synthesize the kettle repair, the red-atlas memory, and the promise about Minami. State who knows each and why each matters now.", "terms": ["blue kettle", "red atlas", "stop arranging"], "forbidden": []},
    "knowledge_boundary": {"question": "List only what Natsumi Ōhashi is entitled to know from the story. Do not give her private facts she never learned.", "terms": ["Natsumi"], "forbidden": ["paper crane", "P_STOP_INTERFERING", "red atlas"]},
    "temporal": {"question": "Give the causal order of the date-boundary conversation, the promise, the date mistake, and the promise being invoked.", "terms": ["date", "promise"], "forbidden": []},
    "character_state": {"question": "Describe Arro and Akari's current trust and misunderstanding without resetting them to their first meeting.", "terms": ["Akari", "misunderstanding"], "forbidden": []},
    "friend_first": {"question": "Continue a scene where someone shows Arro romantic interest. Preserve his friend-first premise, but let Minami push back and retain agency.", "terms": ["Minami"], "forbidden": ["secretly manipulating"]},
    "emotional_residue": {"question": "Write the next scene after Akari's kitchen argument. Carry the emotional residue without an exposition dump or instant reconciliation.", "terms": ["Akari"], "forbidden": []},
    "callback_naturalness": {"question": "Make a restrained callback to the oldest relevant private memory. Do not mention chapter numbers or token counts.", "terms": ["remember"], "forbidden": ["173 chapters", "token 500000"]},
    "narrative_continuation": {"question": "Continue the current school scene in original prose. Preserve POV, tense, slow-burn pacing, character agency, and unresolved threads. Do not summarize the entire history.", "terms": ["Arro"], "forbidden": ["as an AI", "chapter summary"]},
    "repetition": {"question": "Write a 300-word scene with varied sentence openings and dialogue beats; avoid repeating a paragraph structure.", "terms": ["Arro"], "forbidden": []},
    "lost_middle": {"question": "What private memory did Shiori share, and which characters are not entitled to know it? Answer before writing two paragraphs of scene.", "terms": ["red atlas", "Shiori"], "forbidden": ["Akari knows the paper crane"]},
    "standalone_loop": {"question": "Act as planner, scene architect, writer, continuity auditor, and reviser in compact labeled sections for the next scene. Keep the labels brief and preserve the story state.", "terms": ["plan", "Arro"], "forbidden": []},
}


def _event_text(event: dict) -> str:
    facts = "; ".join(event.get("facts_created", []))
    people = ", ".join(event.get("participants", []))
    return f"[Ledger {event['event_id']}] {people} at {event['location']}: {facts}."


def build_story(target_tokens: int, seed: int = 101) -> str:
    """Build a nested story; token positions are approximate (four chars/token)."""
    rng = random.Random(seed)
    header = (
        "STORY BIBLE — ORIGINAL SYNTHETIC EVALUATION\n"
        "Seishun Academy runs a monitored third-year Marriage Practical. Arro and Akari share a room and common spaces; Shiori is Arro's childhood friend; Minami is Arro's handsome male best friend. Arro sincerely tries to help Minami find a girlfriend before noticing his own opportunities. Everyone has agency; no one is omniscient.\n"
        "VOICE RULES: restrained third-person past tense, concrete sensory details, quick but kind dialogue, slow-burn emotional change, no instant confession, no harem, no source-text imitation.\n"
        "CANON STATE: preserve knowledge boundaries, promises, possessions, injuries, locations, and relationship residue.\n\n"
    )
    target_chars = max(1800, target_tokens * 4)
    ledger = sorted(events(), key=lambda e: e["token_region"])
    pieces: list[str] = [header]
    current = len(header)
    event_index = 0
    chapter = 1
    while current < target_chars:
        next_event = ledger[event_index] if event_index < len(ledger) else None
        desired = (next_event["token_region"] * 4) if next_event else target_chars
        if desired > target_chars:
            next_event = None
            desired = target_chars
        while current < min(desired, target_chars):
            place = ["the east stairwell", "a sunlit classroom", "the laundry room", "the covered walkway", "the quiet end of the gym"][chapter % 5]
            sensory = ["rain ticked on the awning", "the vending machine clicked", "chalk dust warmed in the sun", "a bicycle bell crossed the courtyard"][chapter % 4]
            line = f"Chapter {chapter}, scene {chapter % 7 + 1}: At {place}, the group negotiated an ordinary problem while {sensory}. Arro listened, offered one practical suggestion, and nearly turned it into a plan for Minami. Akari noticed the hesitation; Shiori noticed what he left unsaid. The day moved on without resolving everything.\n"
            pieces.append(line)
            current += len(line)
            chapter += 1
        if next_event and current < target_chars:
            line = _event_text(next_event) + "\n"
            pieces.append(line)
            current += len(line)
            event_index += 1
    text = "".join(pieces)
    # Stable deterministic tail; this is deliberately not a copied passage.
    while len(text) < target_chars:
        text += f"The next bell found them still arguing gently about what care required. Detail {rng.randrange(100000)} stayed unresolved.\n"
    return text[:target_chars]


def build_fixture(target_tokens: int, scenario: str, seed: int = 101, sample: int = 0) -> dict:
    if scenario not in SCENARIOS:
        raise KeyError(f"unknown scenario: {scenario}")
    spec = SCENARIOS[scenario]
    story = build_story(target_tokens, seed)
    request = (
        "You are evaluating long-form story state, not reciting a benchmark. "
        "First answer the continuity task in 2–5 precise sentences, then follow the scene instruction. "
        "Use only facts a character could have learned.\n\n"
        f"CONTINUITY TASK: {spec['question']}\n\n"
        "STORY:\n" + story + "\nCURRENT REQUEST:\n" + spec["question"]
    )
    fixture_id = hashlib.sha256(f"{target_tokens}|{scenario}|{seed}|{sample}".encode()).hexdigest()[:16]
    return {
        "fixture_id": fixture_id,
        "target_tokens": target_tokens,
        "scenario": scenario,
        "seed": seed,
        "sample": sample,
        "prompt": request,
        "expected_terms": spec["terms"],
        "forbidden_terms": spec["forbidden"],
        "story_chars": len(story),
    }
