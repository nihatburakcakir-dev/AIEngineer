"""Phase 11: one intentional path from a screenshot to a Unity game request.

The pipeline does not pretend that a visual model can infer every mechanic from
pixels.  It preserves the visual evidence, resolves the explicitly requested
game family, and emits a staged build request which the Unity-side builder can
validate in Play Mode.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from Source.Core.Fusion.visual_fusion import VisualFusionEngine
from Source.Core.Game.game_pipeline import GameGenerationPipeline


@dataclass(frozen=True)
class ReferencePrototypeEvaluation:
    """Deterministic acceptance check for the Unity builder's reported result."""

    valid: bool
    message: str
    missing: tuple[str, ...] = ()

    @classmethod
    def from_unity_result(cls, result: dict[str, Any], expected_scene: str, acceptance_signals: list[str]):
        missing = []
        if not result.get("compiled"):
            missing.append("compiled")
        if not result.get("play_mode_verified"):
            missing.append("play_mode_verified")
        if Path(str(result.get("scene_path", ""))).as_posix() != Path(expected_scene).as_posix():
            missing.append("scene_path")
        observed = set(result.get("acceptance_signals", []))
        if not set(acceptance_signals).issubset(observed):
            missing.append("gameplay_acceptance_signals")
        if missing:
            return cls(False, "Unity prototype validation is incomplete: " + ", ".join(missing), tuple(missing))
        return cls(True, "Compiled scene passed Play Mode and the requested gameplay signals.")


class EndToEndGamePipeline:
    """Combines Phase 5 perception, Phase 7 scaffolding and Phase 2 validation."""

    PHASE_CHAIN = ("phase5_visual_analysis", "phase7_game_generation", "phase2_autonomous_validation")

    def __init__(self, vision_client=None, visual_fusion=None, game_pipeline=None):
        self.visual_fusion = visual_fusion or VisualFusionEngine(vision_client=vision_client)
        self.game_pipeline = game_pipeline or GameGenerationPipeline()

    def attach(self, command, image_path: str | Path, name: str | None = None):
        analysis, visual_plan = self.visual_fusion.analyze_and_plan(image_path)
        game_plan = self.game_pipeline.plan(command.prompt, name)
        game_request = self.game_pipeline.scaffolder.build_request(game_plan)

        command.intent = "BUILD_GAME_FROM_REFERENCE"
        command.target = game_plan.game_name
        command.parameters["image_path"] = str(image_path)
        command.metadata["visual_analysis"] = analysis.to_dict()
        command.metadata["visual_build_plan"] = visual_plan.to_dict()
        command.metadata["game_scaffold_plan"] = game_plan.to_dict()
        command.metadata["game_build_request"] = game_request
        command.metadata["end_to_end_game_plan"] = {
            "phase_chain": list(self.PHASE_CHAIN),
            "reference_image": str(image_path),
            "visual_summary": visual_plan.summary,
            "game_key": game_plan.game_key,
            "scene_path": game_plan.scene_path,
            "acceptance_signals": list(game_plan.acceptance_signals),
            "requires_unity_validation": True,
        }
        return command
