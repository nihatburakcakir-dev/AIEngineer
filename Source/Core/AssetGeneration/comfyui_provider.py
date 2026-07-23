"""Local ComfyUI API provider using an exported API workflow template."""

from __future__ import annotations

import json
from pathlib import Path
import secrets
import time
from typing import Any, Callable
from uuid import uuid4
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .asset_generation_result import AssetGenerationResult
from .asset_provider import AssetProviderError, ImageGenerationRequest


class ComfyUiProvider:
    """Generate an image through ComfyUI's local `/prompt` and `/history` APIs.

    The workflow must be an API-format JSON export. String tokens `$prompt`,
    `$model`, `$width`, `$height` and `$transparent` are replaced recursively before it is
    submitted, keeping model-specific node layouts outside application code.
    """

    name = "comfyui"

    def __init__(self, endpoint: str, workflow_path: str, timeout: int = 180,
                 transport: Callable[[str, str, bytes | None], bytes] | None = None,
                 reference_workflow_path: str = ""):
        self.endpoint = endpoint.rstrip("/")
        self.workflow_path = Path(workflow_path)
        self.timeout = timeout
        self.transport = transport or self._transport
        self.reference_workflow_path = Path(reference_workflow_path) if reference_workflow_path else None

    def generate_image(self, request: ImageGenerationRequest) -> AssetGenerationResult:
        workflow_path = self._workflow_for(request)
        target = self._target_path(request)
        if target.exists() and not request.overwrite:
            raise AssetProviderError(f"Refusing to overwrite generated image without overwrite=true: {request.output_path}")
        reference_name = self._upload_reference(request) if request.reference_image_path else ""
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        payload = json.dumps({"prompt": self._substitute(workflow, request, reference_name)}).encode("utf-8")
        submitted = json.loads(self.transport("POST", "/prompt", payload).decode("utf-8"))
        prompt_id = str(submitted.get("prompt_id", ""))
        if not prompt_id:
            raise AssetProviderError("ComfyUI accepted no prompt_id: " + json.dumps(submitted))
        image = self._wait_for_image(prompt_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(image)
        return AssetGenerationResult(request.output_path, "image/png", self.name, {"prompt_id": prompt_id})

    def _wait_for_image(self, prompt_id: str) -> bytes:
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            history = json.loads(self.transport("GET", "/history/" + prompt_id, None).decode("utf-8"))
            entry = history.get(prompt_id, {}) if isinstance(history, dict) else {}
            if entry.get("status", {}).get("status_str") == "error":
                raise AssetProviderError("ComfyUI generation failed: " + json.dumps(entry.get("status", {})))
            for output in entry.get("outputs", {}).values():
                images = output.get("images", []) if isinstance(output, dict) else []
                if images:
                    image = images[0]
                    query = urlencode({key: image[key] for key in ("filename", "subfolder", "type") if image.get(key)})
                    return self.transport("GET", "/view?" + query, None)
            time.sleep(0.5)
        raise AssetProviderError(f"ComfyUI timed out after {self.timeout}s while generating image {prompt_id}.")

    def _workflow_for(self, request: ImageGenerationRequest) -> Path:
        workflow_path = self.reference_workflow_path if request.reference_image_path else self.workflow_path
        if workflow_path is None or not workflow_path.is_file():
            mode = "reference" if request.reference_image_path else "generation"
            raise AssetProviderError(f"ComfyUI {mode} workflow was not found: {workflow_path}")
        return workflow_path

    def _upload_reference(self, request: ImageGenerationRequest) -> str:
        source = Path(request.reference_image_path)
        if not source.is_file():
            raise AssetProviderError(f"Reference image was not found: {source}")
        if source.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise AssetProviderError("Reference image must be PNG, JPG, JPEG or WEBP.")
        boundary = "----AIEngineer" + uuid4().hex
        safe_name = "AIEngineer_" + uuid4().hex + source.suffix.lower()
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="image"; filename="{safe_name}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8") + source.read_bytes() + f"\r\n--{boundary}--\r\n".encode("utf-8")
        upload = Request(self.endpoint + "/upload/image", data=body, method="POST")
        upload.add_header("Content-Type", "multipart/form-data; boundary=" + boundary)
        try:
            with urlopen(upload, timeout=min(self.timeout, 30)) as response:
                result = json.loads(response.read().decode("utf-8"))
        except OSError as error:
            raise AssetProviderError(f"ComfyUI could not receive the reference image: {error}") from error
        name = str(result.get("name", ""))
        if not name:
            raise AssetProviderError("ComfyUI accepted no filename for the reference image.")
        return name

    @staticmethod
    def _substitute(value: Any, request: ImageGenerationRequest, reference_name: str = "") -> Any:
        replacements = {
            "$prompt": request.prompt, "$model": request.model, "$width": request.width,
            "$height": request.height, "$transparent": request.transparent,
            "$seed": secrets.randbelow(2**63), "$reference_image": reference_name,
            "$edit_strength": request.edit_strength,
        }
        if isinstance(value, str):
            return replacements.get(value, value)
        if isinstance(value, list):
            return [ComfyUiProvider._substitute(item, request, reference_name) for item in value]
        if isinstance(value, dict):
            return {key: ComfyUiProvider._substitute(item, request, reference_name) for key, item in value.items()}
        return value

    @staticmethod
    def _target_path(request: ImageGenerationRequest) -> Path:
        root = Path(request.project_root).resolve()
        target = (root / request.output_path).resolve()
        assets = (root / "Assets").resolve()
        if not request.project_root or assets not in target.parents:
            raise AssetProviderError("Generated image output escapes the Unity Assets directory.")
        return target

    def _transport(self, method: str, path: str, data: bytes | None) -> bytes:
        request = Request(self.endpoint + path, data=data, method=method)
        if data is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with urlopen(request, timeout=min(self.timeout, 30)) as response:
                return response.read()
        except OSError as error:
            raise AssetProviderError(f"ComfyUI is unavailable at {self.endpoint}: {error}") from error
