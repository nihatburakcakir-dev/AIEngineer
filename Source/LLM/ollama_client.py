"""Local-only Ollama text client used by planning and code-generation tasks."""

import json
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import URLError
from urllib.request import Request, urlopen


_OPERATION_REQUIRED_FIELDS = {
    "write_text": ("path", "content"),
    "replace_text": ("path", "search", "replacement"),
    "delete_asset": ("path",),
    "create_folder": ("path",),
    "create_scene": ("path",),
    "create_game_object": ("name",),
    "add_component": ("targetPath", "component"),
    "set_property": ("targetPath", "property"),
    "create_prefab": ("assetPath", "name"),
    "instantiate_prefab": ("assetPath",),
    "create_material": ("assetPath",),
    "create_effect": ("name",),
    "create_ui_screen": ("name", "title"),
    "build_character": ("name", "sourceImagePath", "dimension"),
    "generate_prototype": ("gameKey", "name"),
    "save_scene": (),
}


def _operation_variant(kind, required_fields):
    properties = {
        "id": {"type": "string"},
        "kind": {"type": "string", "enum": [kind]},
    }
    for field_name in required_fields:
        properties[field_name] = {"type": "string", "minLength": 1}
    return {
        "type": "object",
        "required": ["id", "kind", *required_fields],
        "properties": properties,
        "additionalProperties": True,
    }


OPERATION_SCHEMAS = [
    _operation_variant(kind, required_fields)
    for kind, required_fields in _OPERATION_REQUIRED_FIELDS.items()
]


CHANGE_SET_SCHEMA = {
    "type": "object",
    "required": [
        "protocol", "responseType", "requestId", "summary", "answer", "risk",
        "requiresConfirmation", "operations", "validation", "explanation", "warnings",
    ],
    "properties": {
        "protocol": {"type": "string", "enum": ["ai-engineer.change-set/v1"]},
        "responseType": {"type": "string", "enum": ["answer", "change_set"]},
        "requestId": {"type": "string"},
        "summary": {"type": "string"},
        "answer": {"type": "string"},
        "risk": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
        "requiresConfirmation": {"type": "boolean"},
        "operations": {
            "type": "array",
            "maxItems": 48,
            "items": {"oneOf": OPERATION_SCHEMAS},
        },
        "validation": {
            "type": "object",
            "required": ["compile", "playMode", "checks"],
            "properties": {
                "compile": {"type": "boolean"},
                "playMode": {"type": "boolean"},
                "checks": {"type": "array", "items": {"type": "string"}},
            },
        },
        "explanation": {"type": "array", "items": {"type": "string"}},
        "warnings": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": False,
}

FEATURE_ANALYSIS_SCHEMA = {
    "type": "object",
    "required": ["behavior", "distribution", "feedback", "integration", "acceptance"],
    "properties": {
        "behavior": {"type": "array", "items": {"type": "string"}},
        "distribution": {"type": "array", "items": {"type": "string"}},
        "feedback": {"type": "array", "items": {"type": "string"}},
        "integration": {"type": "array", "items": {"type": "string"}},
        "acceptance": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": False,
}


class LocalModelUnavailable(RuntimeError):
    """Raised when a local model cannot be reached; no cloud fallback is attempted."""


@dataclass(frozen=True)
class LocalModelStatus:
    available: bool
    models: tuple[str, ...]
    endpoint: str
    message: str = ""


class OllamaClient:
    def __init__(self, model="qwen3:30b", endpoint="http://127.0.0.1:11434/api/chat", transport: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None, timeout=90):
        self.model = model
        self.endpoint = endpoint
        self.transport = transport or self._transport
        self.timeout = timeout

    def generate(self, prompt: str, system: str = "", task: str = "chat") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        # Planning responses are structured manifests, not open-ended chats. A bounded
        # response prevents a local model from spending several minutes elaborating a
        # plan that Unity will reject unless it is valid JSON.
        # Feature work can legitimately contain a compact runtime script plus its
        # prefab/effect wiring.  2K tokens truncates those otherwise valid plans.
        output_limit = 128 if task == "retrieval" else (1536 if task == "feature_analysis" else (6144 if task in {"planning", "code_generation"} else 2048))
        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "messages": messages,
            "options": {"temperature": 0, "num_predict": output_limit},
        }
        if task in {"planning", "code_generation"}:
            # Ollama structured output prevents the model from returning a chat
            # envelope such as {role, content} where an executable protocol object
            # is required. The Python parser still performs the security checks.
            payload["format"] = CHANGE_SET_SCHEMA
        elif task == "feature_analysis":
            payload["format"] = FEATURE_ANALYSIS_SCHEMA
        response = self.transport(self.endpoint, payload)
        content = response.get("message", {}).get("content") if isinstance(response, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise LocalModelUnavailable(f"Local model '{self.model}' returned no usable text for {task}.")
        return content.strip()

    def status(self) -> LocalModelStatus:
        tags_endpoint = self.endpoint.rsplit("/", 1)[0] + "/tags"
        try:
            response = self.transport(tags_endpoint, {})
        except LocalModelUnavailable as error:
            return LocalModelStatus(False, (), self.endpoint, str(error))
        models = tuple(item.get("name", "") for item in response.get("models", []) if item.get("name"))
        return LocalModelStatus(self.model in models, models, self.endpoint, "" if self.model in models else f"Model '{self.model}' is not installed locally.")

    def _transport(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        data = None if endpoint.endswith("/tags") else json.dumps(payload).encode("utf-8")
        request = Request(endpoint, data=data, headers={"Content-Type": "application/json"}, method="GET" if data is None else "POST")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, json.JSONDecodeError) as error:
            raise LocalModelUnavailable(f"Local Ollama service is unavailable at {endpoint}. Start Ollama and install '{self.model}'.") from error
