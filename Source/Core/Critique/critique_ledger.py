"""Append-only handoff records for the Phase 10 learning/memory module."""

import json
from datetime import datetime, timezone
from pathlib import Path


class CritiqueLedger:
    def __init__(self, path="Data/critique_events.jsonl"):
        self.path = Path(path)

    def record(self, command, warnings):
        if not warnings:
            return None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "phase": 9,
            "intent": command.intent,
            "prompt": command.prompt,
            "warnings": warnings,
            "memory_status": "pending_phase_10_import",
        }
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event
