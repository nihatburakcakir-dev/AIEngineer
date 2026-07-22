"""Typed, serialisable output from the visual-perception boundary."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class UIElement:
    kind: str
    label: str = ""
    layout: str = ""
    anchor: str = ""
    confidence: float = 0.0


@dataclass
class SceneComposition:
    objects: list[str] = field(default_factory=list)
    composition: str = ""
    depth: str = ""
    confidence: float = 0.0


@dataclass
class AssetStyle:
    dimension: str = "unknown"
    style: str = ""
    asset_types: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class CameraAnalysis:
    angle: str = "unknown"
    projection: str = "unknown"
    framing: str = ""
    confidence: float = 0.0


@dataclass
class LightingAnalysis:
    direction: str = ""
    color: str = ""
    atmosphere: str = ""
    confidence: float = 0.0


@dataclass
class VisualAnalysis:
    image_path: str
    image_size: tuple[int, int] | None
    ui: list[UIElement] = field(default_factory=list)
    scene: SceneComposition = field(default_factory=SceneComposition)
    assets: AssetStyle = field(default_factory=AssetStyle)
    camera: CameraAnalysis = field(default_factory=CameraAnalysis)
    lighting: LightingAnalysis = field(default_factory=LightingAnalysis)
    model: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
