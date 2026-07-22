"""Strict parser for structured output returned by a vision model."""

import json
from pathlib import Path
from typing import Any

from Source.Core.Vision.models import AssetStyle, CameraAnalysis, LightingAnalysis, SceneComposition, UIElement, VisualAnalysis


class ImageParseError(ValueError):
    pass


class ImageParser:
    REQUIRED_SECTIONS = ("ui", "scene", "assets", "camera", "lighting")

    def parse(self, image_path: str | Path, response: dict[str, Any] | str, model: str = "") -> VisualAnalysis:
        data = self._normalise(self._as_json(response))
        missing = [section for section in self.REQUIRED_SECTIONS if section not in data]
        if missing:
            raise ImageParseError(f"Vision response is missing required sections: {', '.join(missing)}")
        ui_data = data["ui"]
        if not isinstance(ui_data, list):
            raise ImageParseError("Vision response field 'ui' must be a list.")
        return VisualAnalysis(
            image_path=str(image_path), image_size=self.image_size(image_path),
            ui=[UIElement(**self._allowed(item, {"kind", "label", "layout", "anchor", "confidence"})) for item in ui_data],
            scene=SceneComposition(**self._allowed(data["scene"], {"objects", "composition", "depth", "confidence"})),
            assets=AssetStyle(**self._allowed(data["assets"], {"dimension", "style", "asset_types", "confidence"})),
            camera=CameraAnalysis(**self._allowed(data["camera"], {"angle", "projection", "framing", "confidence"})),
            lighting=LightingAnalysis(**self._allowed(data["lighting"], {"direction", "color", "atmosphere", "confidence"})),
            model=model, raw=data,
        )

    @staticmethod
    def _as_json(response: dict[str, Any] | str) -> dict[str, Any]:
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError as error:
                raise ImageParseError(f"Vision response is not valid JSON: {error.msg}") from error
        if not isinstance(response, dict):
            raise ImageParseError("Vision response must be a JSON object.")
        return response

    @staticmethod
    def _allowed(value: Any, keys: set[str]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ImageParseError("Each visual-analysis section must be a JSON object.")
        return {key: value[key] for key in keys if key in value}

    @staticmethod
    def _normalise(data: dict[str, Any]) -> dict[str, Any]:
        """Tolerate common local-model aliases without accepting missing dimensions."""
        data = dict(data)
        ui = data.get("ui", [])
        if isinstance(ui, dict):
            ui = ui.get("elements", ui.get("items", [ui]))
        if isinstance(ui, str):
            ui = [ui]
        if isinstance(ui, list):
            normalized_ui = []
            for item in ui:
                if not isinstance(item, dict):
                    normalized_ui.append({"kind": "other", "label": str(item), "confidence": 0.0})
                    continue
                element = dict(item)
                # A vision model can identify an element yet omit its category.
                # Keep the evidence available to the planner instead of failing the
                # entire request over one optional classification field.
                element.setdefault("kind", "other")
                element.setdefault("label", "")
                element.setdefault("layout", "")
                element.setdefault("anchor", "")
                element.setdefault("confidence", 0.0)
                normalized_ui.append(element)
            data["ui"] = normalized_ui

        assets = data.get("assets")
        if isinstance(assets, dict):
            assets = dict(assets)
            if "asset_types" not in assets:
                assets["asset_types"] = list(assets.get("models", [])) + list(assets.get("textures", []))
            if "dimension" not in assets and assets.get("models"):
                assets["dimension"] = "3D"
            if str(assets.get("dimension", "")).casefold().replace(" ", "") in {"2d|3d|mixed", "2d/3d", "2d+3d"}:
                assets["dimension"] = "mixed"
            data["assets"] = assets

        camera = data.get("camera")
        if isinstance(camera, dict):
            data["camera"] = dict(camera)

        lighting = data.get("lighting")
        if isinstance(lighting, dict):
            lighting = dict(lighting)
            ambient = lighting.get("ambient", {})
            if isinstance(ambient, dict):
                lighting.setdefault("color", ambient.get("color", ""))
                lighting.setdefault("atmosphere", "ambient lighting")
            data["lighting"] = lighting
        return data

    @staticmethod
    def image_size(image_path: str | Path) -> tuple[int, int] | None:
        """Read PNG/GIF dimensions without a Pillow runtime dependency."""
        path = Path(image_path)
        if not path.is_file():
            raise FileNotFoundError(f"Image does not exist: {path}")
        with path.open("rb") as image:
            header = image.read(32)
        if header.startswith(b"\x89PNG\r\n\x1a\n") and len(header) >= 24:
            return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")
        if header.startswith(b"GIF") and len(header) >= 10:
            return int.from_bytes(header[6:8], "little"), int.from_bytes(header[8:10], "little")
        if header.startswith(b"\xff\xd8"):
            return ImageParser._jpeg_size(path)
        return None

    @staticmethod
    def _jpeg_size(path: Path) -> tuple[int, int] | None:
        data = path.read_bytes()
        index = 2
        sof_markers = {*range(0xC0, 0xC4), *range(0xC5, 0xC8), *range(0xC9, 0xCC), *range(0xCD, 0xD0)}
        while index + 9 < len(data):
            if data[index] != 0xFF:
                index += 1
                continue
            marker = data[index + 1]
            index += 2
            if marker in {0xD8, 0xD9}:
                continue
            if index + 2 > len(data):
                return None
            segment_length = int.from_bytes(data[index:index + 2], "big")
            if marker in sof_markers and index + 7 <= len(data):
                return int.from_bytes(data[index + 5:index + 7], "big"), int.from_bytes(data[index + 3:index + 5], "big")
            index += max(segment_length, 2)
        return None
