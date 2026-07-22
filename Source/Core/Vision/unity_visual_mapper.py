"""Convert visual evidence into explicit, reviewable Unity construction commands."""

from dataclasses import dataclass, field

from Source.Core.Vision.models import VisualAnalysis


@dataclass
class VisualBuildPlan:
    summary: str
    commands: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unity_context: dict = field(default_factory=dict)

    def to_dict(self):
        return {"summary": self.summary, "commands": self.commands, "warnings": self.warnings, "unity_context": self.unity_context}


class UnityVisualMapper:
    """Maps observed UI, composition, camera, and lighting to Unity concepts."""

    def __init__(self, expertise=None):
        self.expertise = expertise

    def map(self, analysis: VisualAnalysis) -> VisualBuildPlan:
        commands, warnings = [], []
        camera = analysis.camera
        camera_angle = self._canonical_camera_angle(camera.angle)
        camera_projection = self._canonical_projection(camera.projection)
        camera_command = self._camera_command(camera_angle, camera_projection)
        if camera_command:
            if self.expertise and self.expertise.has_package("com.unity.cinemachine"):
                camera_command["camera_system"] = "Cinemachine"
            elif camera_angle.casefold() in {"top-down", "isometric", "first-person", "third-person"}:
                camera_command["suggested_package"] = "com.unity.cinemachine"
                if self.expertise:
                    warnings.append("Cinemachine is not installed; the plan uses Unity Camera settings and marks Cinemachine as an optional follow-camera upgrade.")
            commands.append(camera_command)
        else:
            warnings.append("Camera type is uncertain; keep the existing camera until the reference is reviewed.")

        ui_commands = self._ui_commands(analysis)
        commands.extend(ui_commands)
        if analysis.ui and not ui_commands:
            warnings.append("UI elements were found but their layout is uncertain; do not create a fixed-position layout automatically.")

        if analysis.scene.objects:
            commands.append({"action": "compose_scene", "objects": analysis.scene.objects, "composition": analysis.scene.composition, "risk": "MEDIUM"})
        if analysis.assets.dimension.casefold() in {"2d", "3d", "mixed"}:
            commands.append({"action": "set_art_direction", "dimension": analysis.assets.dimension, "style": analysis.assets.style, "asset_types": analysis.assets.asset_types, "risk": "LOW"})
        if any((analysis.lighting.direction, analysis.lighting.color, analysis.lighting.atmosphere)):
            commands.append({"action": "configure_lighting", "direction": analysis.lighting.direction, "color": analysis.lighting.color, "atmosphere": analysis.lighting.atmosphere, "risk": "LOW"})

        summary = f"{camera_angle or 'Unknown'} camera; {len(analysis.ui)} UI element(s); {analysis.assets.dimension} assets."
        request = " ".join([camera_angle, camera_projection, "ui canvas grid layout", analysis.assets.dimension, analysis.assets.style]).strip()
        unity_context = self.expertise.context_for(request) if self.expertise else {}
        return VisualBuildPlan(summary=summary, commands=commands, warnings=warnings, unity_context=unity_context)

    @staticmethod
    def _canonical_camera_angle(value: str) -> str:
        normalized = (value or "").casefold().replace("_", "-")
        aliases = {
            "top-down": ("top-down", "top down", "bird's-eye", "birds-eye", "overhead"),
            "side-scroll": ("side-scroll", "side scroll", "side-view", "side view"),
            "first-person": ("first-person", "first person"),
            "third-person": ("third-person", "third person"),
            "isometric": ("isometric",),
        }
        for canonical, values in aliases.items():
            if any(candidate in normalized for candidate in values):
                return canonical
        return value or "unknown"

    @staticmethod
    def _canonical_projection(value: str) -> str:
        normalized = (value or "").casefold()
        if "orthographic" in normalized:
            return "orthographic"
        if "perspective" in normalized:
            return "perspective"
        return value or "unknown"

    @staticmethod
    def _camera_command(angle: str, projection: str) -> dict | None:
        normalized = (angle or "").casefold()
        if normalized in {"top-down", "isometric"}:
            return {"action": "create_camera", "projection": "Orthographic" if projection.casefold() != "perspective" else "Perspective", "angle": angle, "rotation": [45, 0, 0] if normalized == "isometric" else [90, 0, 0], "risk": "LOW"}
        if normalized == "side-scroll":
            return {"action": "create_camera", "projection": "Orthographic", "angle": angle, "rotation": [0, 0, 0], "risk": "LOW"}
        if normalized in {"first-person", "third-person"}:
            return {"action": "create_camera", "projection": "Perspective", "angle": angle, "risk": "LOW"}
        return None

    @staticmethod
    def _ui_commands(analysis: VisualAnalysis) -> list[dict]:
        commands = []
        if not analysis.ui:
            return commands
        recognized = []
        for element in analysis.ui:
            kind = element.kind.casefold().replace("-", "_")
            if kind == "grid":
                recognized.append({"action": "create_ui_grid", "component": "GridLayoutGroup", "label": element.label, "risk": "LOW"})
            elif kind in {"panel", "button", "label", "health_bar"}:
                recognized.append({"action": "create_ui_element", "kind": kind, "label": element.label, "layout": element.layout, "risk": "LOW"})
        if recognized:
            commands.append({"action": "create_canvas", "render_mode": "ScreenSpaceOverlay", "risk": "LOW"})
            commands.extend(recognized)
        return commands
