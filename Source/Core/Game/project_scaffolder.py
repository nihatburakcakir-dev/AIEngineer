"""Turn a known reference-game template into a reviewable Unity build request."""

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import re

from Source.Core.Game.reference_game_input import ReferenceGameTemplate


@dataclass(frozen=True)
class GameScaffoldPlan:
    game_key: str
    game_name: str
    scene_path: str
    folders: tuple[str, ...]
    systems: tuple[str, ...]
    progress_stages: tuple[str, ...]
    acceptance_signals: tuple[str, ...]

    def to_dict(self):
        return asdict(self)


class ProjectScaffolder:
    # Generated games must remain outside the protected Unity package folder.
    OUTPUT_ROOT = "Assets/AIEngineerGenerated/Games"

    def build_plan(self, template: ReferenceGameTemplate, requested_name: str | None = None) -> GameScaffoldPlan:
        game_name = self._safe_name(requested_name or template.key)
        base = f"{self.OUTPUT_ROOT}/{game_name}"
        return GameScaffoldPlan(
            game_key=template.key,
            game_name=game_name,
            scene_path=f"{base}/{game_name}.unity",
            folders=(base, f"{base}/Scripts", f"{base}/Prefabs", f"{base}/Materials"),
            systems=template.systems,
            progress_stages=(
                "template_resolved", "scene_scaffolded", "core_mechanics_created",
                "ui_created", "play_mode_verified",
            ),
            acceptance_signals=template.acceptance_signals,
        )

    def build_request(self, plan: GameScaffoldPlan) -> dict:
        return {
            "gameKey": plan.game_key,
            "gameName": plan.game_name,
            "scenePath": plan.scene_path,
            "systems": list(plan.systems),
            "acceptanceSignals": list(plan.acceptance_signals),
            "autoPlayValidation": True,
        }

    def write_request(self, plan: GameScaffoldPlan, output_path: str | Path) -> Path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.build_request(plan), indent=2), encoding="utf-8")
        return output

    @staticmethod
    def _safe_name(value: str) -> str:
        words = re.findall(r"[A-Za-z0-9]+", value)
        return "".join(word.capitalize() for word in words) or "GeneratedGame"
