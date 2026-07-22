"""Local-first client for a structured multimodal model (Ollama compatible)."""

import base64
import json
from pathlib import Path
from typing import Any, Callable
from urllib.request import Request, urlopen

from Source.Core.Vision.image_parser import ImageParseError, ImageParser


class VisionClient:
    """Calls a local multimodal model and refuses unstructured/failed perception."""

    STRUCTURED_PROMPT = """Analyze this game screenshot. Return JSON only with this exact shape:
{\"ui\":[{\"kind\":\"\",\"label\":\"\",\"layout\":\"\",\"anchor\":\"top_left|top_center|top_right|center_left|center|center_right|bottom_left|bottom_center|bottom_right\",\"confidence\":0.0}],\"scene\":{\"objects\":[\"\"],\"composition\":\"\",\"depth\":\"\",\"confidence\":0.0},\"assets\":{\"dimension\":\"2D|3D|mixed\",\"style\":\"\",\"asset_types\":[\"\"],\"confidence\":0.0},\"camera\":{\"angle\":\"top-down|side-scroll|first-person|third-person|isometric|other\",\"projection\":\"orthographic|perspective|unknown\",\"framing\":\"\",\"confidence\":0.0},\"lighting\":{\"direction\":\"\",\"color\":\"\",\"atmosphere\":\"\",\"confidence\":0.0}}.
Use only visible evidence. Keep strings short. Use [] or empty strings when uncertain; never omit a key."""

    REPAIR_PROMPT = """Return JSON only using the exact required shape. Include ui, scene, assets, camera and lighting. Specifically state camera.angle, camera.projection, assets.dimension, and lighting.atmosphere from visible evidence; use unknown or empty only if truly not visible."""

    def __init__(self, model: str = "llava:7b", endpoint: str = "http://127.0.0.1:11434/api/chat", transport: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None, retries: int = 2):
        self.model, self.endpoint = model, endpoint
        self.transport = transport or self._ollama_transport
        self.parser = ImageParser()
        self.retries = retries

    def analyze(self, image_path: str | Path):
        path = Path(image_path)
        if not path.is_file():
            raise FileNotFoundError(f"Image does not exist: {path}")
        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0, "num_predict": 1024},
            "messages": [{"role": "user", "content": self.STRUCTURED_PROMPT, "images": [self._image_data(path)]}],
        }
        last_error = None
        best_analysis = None
        for attempt in range(self.retries + 1):
            result = self.transport(payload)
            if isinstance(result, dict) and result.get("done") is False:
                last_error = ImageParseError("Local vision model returned an unfinished response.")
                if attempt == self.retries:
                    if best_analysis is not None:
                        return best_analysis
                    raise last_error
                payload["messages"][0]["content"] = self.REPAIR_PROMPT
                continue
            content = result.get("message", {}).get("content", result) if isinstance(result, dict) else result
            try:
                analysis = self.parser.parse(path, content, model=self.model)
                if self._has_core_evidence(analysis):
                    return analysis
                best_analysis = analysis
                if attempt == self.retries:
                    return best_analysis
                payload["messages"][0]["content"] = self.REPAIR_PROMPT
                continue
            except ImageParseError as error:
                last_error = error
                if attempt == self.retries:
                    if best_analysis is not None:
                        return best_analysis
                    raise
                payload["messages"][0]["content"] = self.REPAIR_PROMPT
        raise last_error

    @staticmethod
    def _has_core_evidence(analysis) -> bool:
        return analysis.camera.angle not in {"", "unknown"} and analysis.assets.dimension not in {"", "unknown"}

    def _ollama_transport(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(self.endpoint, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except OSError as error:
            raise RuntimeError(f"Local vision model is unavailable at {self.endpoint}. Start Ollama with a multimodal model such as '{self.model}'.") from error

    @staticmethod
    def _image_data(path: Path) -> str:
        return base64.b64encode(path.read_bytes()).decode("ascii")
