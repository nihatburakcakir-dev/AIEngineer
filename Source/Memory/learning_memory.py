"""Persistent lessons extracted from task outcomes and Phase 9 critique records."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from Source.Memory.models import LearnedLesson


class LearningMemory:
    def __init__(self, critique_path="Data/critique_events.jsonl", memory_path="Data/learning_memory.json", outcomes_path="Data/task_outcomes.jsonl", rules_path="Data/learned_unity_rules.json"):
        self.critique_path = Path(critique_path)
        self.memory_path = Path(memory_path)
        self.outcomes_path = Path(outcomes_path)
        self.rules_path = Path(rules_path)

    def import_critique_events(self):
        grouped = {}
        for event in self._json_lines(self.critique_path):
            for warning in event.get("warnings", []):
                if not self._warning_matches_prompt(warning.get("code", ""), event):
                    continue
                code = warning.get("code", "unknown")
                lesson = grouped.setdefault(code, LearnedLesson(
                    code=code,
                    severity=warning.get("severity", "MEDIUM"),
                    lesson=warning.get("rationale", warning.get("issue", "")),
                    alternative=warning.get("alternative", ""),
                ))
                lesson.occurrences += 1 if lesson.example_prompts else 0
                prompt = event.get("prompt", "")
                if prompt and prompt not in lesson.example_prompts:
                    lesson.example_prompts.append(prompt)
        lessons = sorted(grouped.values(), key=lambda item: (-item.occurrences, item.code))
        self._write_memory(lessons)
        self.promote_recurring_rules(lessons)
        return lessons

    def lessons(self):
        if not self.memory_path.is_file():
            return self.import_critique_events()
        data = json.loads(self.memory_path.read_text(encoding="utf-8"))
        return [LearnedLesson(**item) for item in data.get("lessons", [])]

    def relevant_for(self, prompt):
        request_tokens = self._tokens(prompt)
        relevant = []
        for lesson in self.lessons():
            evidence = set()
            for example in lesson.example_prompts:
                evidence.update(self._tokens(example))
            specific_evidence = evidence - {"update", "every", "frame", "her", "içinde", "icinde", "ile", "new", "object"}
            if self._code_matches(lesson.code, request_tokens) or request_tokens & specific_evidence:
                relevant.append(lesson)
        return relevant

    def record_execution(self, plan, result):
        self.outcomes_path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "intent": plan.action,
            "target": plan.target,
            "warnings": plan.warnings,
            "success": result.success,
            "failure": "" if result.success else result.perception.message,
            "resolution": result.perception.message if result.success else "pending_repair_or_manual_review",
        }
        with self.outcomes_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event

    def _write_memory(self, lessons):
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"updated_utc": datetime.now(timezone.utc).isoformat(), "lessons": [lesson.to_dict() for lesson in lessons]}
        self.memory_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def promote_recurring_rules(self, lessons=None, minimum_occurrences=2):
        lessons = lessons if lessons is not None else self.lessons()
        rules = [
            {"code": lesson.code, "rule": lesson.alternative, "rationale": lesson.lesson, "keywords": self._lesson_keywords(lesson)}
            for lesson in lessons if lesson.occurrences >= minimum_occurrences
        ]
        self.rules_path.parent.mkdir(parents=True, exist_ok=True)
        self.rules_path.write_text(json.dumps({"rules": rules}, ensure_ascii=False, indent=2), encoding="utf-8")
        return rules

    @staticmethod
    def _json_lines(path):
        if not path.is_file():
            return []
        records = []
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records

    @staticmethod
    def _tokens(value):
        return set(re.findall(r"[a-z0-9_]+", (value or "").casefold()))

    @staticmethod
    def _code_matches(code, tokens):
        hints = {
            "per_frame_allocation": {"instantiate", "destroy", "allocation"},
            "per_frame_component_lookup": {"getcomponent"},
            "physics_in_update": {"rigidbody", "physics", "addforce"},
            "unity_expertise_constraint": {"hdrp", "urp", "material", "shader"},
        }
        return bool(hints.get(code, set()) & tokens)

    @classmethod
    def _warning_matches_prompt(cls, code, event):
        if code.startswith("faz4_") or code == "high_impact_change":
            return True
        prompt_tokens = cls._tokens(event.get("prompt", ""))
        requirements = {
            "per_frame_allocation": {"update", "frame", "instantiate", "destroy"},
            "per_frame_component_lookup": {"getcomponent"},
            "physics_in_update": {"rigidbody", "physics", "addforce"},
            "unity_expertise_constraint": {"hdrp", "urp", "shader", "material"},
        }
        required = requirements.get(code)
        return required is None or bool(prompt_tokens & required)

    @classmethod
    def _lesson_keywords(cls, lesson):
        hints = {
            "per_frame_allocation": ["update", "instantiate", "destroy", "frame"],
            "per_frame_component_lookup": ["update", "getcomponent"],
            "physics_in_update": ["update", "rigidbody", "physics", "addforce"],
        }
        return hints.get(lesson.code, sorted(cls._tokens(" ".join(lesson.example_prompts)))[:8])
