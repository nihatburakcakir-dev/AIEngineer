"""Versioned, bounded protocol between the model and the Unity editor.

The model is never allowed to write to disk directly. It returns a reviewed
change set, this module validates its shape and paths, and Unity applies the
supported operations inside a transaction.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import posixpath
import re
import unicodedata
from typing import Any
from uuid import uuid4


PROTOCOL = "ai-engineer.change-set/v1"
ALLOWED_KINDS = {
    "write_text", "replace_text", "delete_asset", "create_folder",
    "create_scene", "create_game_object", "add_component", "set_property",
    "create_prefab", "instantiate_prefab", "create_material", "create_effect", "create_ui_screen",
    "build_character", "generate_prototype", "save_scene",
}
PATH_FIELDS = ("path", "assetPath", "scenePath")
UNITY_SERIALIZED_EXTENSIONS = {".prefab", ".unity", ".mat", ".asset", ".controller"}
HIGH_RISK_KINDS = {"delete_asset"}
MAX_OPERATIONS = 48
MAX_TEXT_SIZE = 300_000


class ProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class ValidationSpec:
    compile: bool = True
    playMode: bool = False
    checks: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ChangeOperation:
    id: str
    kind: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "kind": self.kind, **self.payload}


@dataclass(frozen=True)
class ChangeSet:
    requestId: str
    summary: str
    risk: str
    requiresConfirmation: bool
    operations: list[ChangeOperation]
    validation: ValidationSpec
    explanation: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    model: str = ""
    responseType: str = "change_set"
    answer: str = ""
    protocol: str = PROTOCOL

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["operations"] = [operation.to_dict() for operation in self.operations]
        return data


class ChangeSetParser:
    """Parse model JSON and reject unsafe or unexecutable instructions."""

    def parse(self, response: str | dict[str, Any], model: str = "") -> ChangeSet:
        data = self._as_object(response)
        protocol = str(data.get("protocol") or PROTOCOL)
        if protocol != PROTOCOL:
            raise ProtocolError(f"Unsupported change-set protocol: {protocol}")
        raw_operations = data.get("operations", [])
        raw_operations, normalization_warnings = self._normalise_ui_operations(raw_operations)
        answer = str(data.get("answer", "")).strip()
        inferred_type = "answer" if answer and isinstance(raw_operations, list) and not raw_operations else "change_set"
        response_type = str(data.get("responseType") or inferred_type).strip().casefold()
        if response_type not in {"answer", "change_set"}:
            raise ProtocolError("responseType must be 'answer' or 'change_set'.")
        if not isinstance(raw_operations, list):
            raise ProtocolError("operations must be an array.")
        if response_type == "answer":
            if not answer:
                raise ProtocolError("An answer response must contain answer text.")
            if raw_operations:
                raise ProtocolError("An answer response cannot also contain operations.")
        elif not raw_operations:
            raise ProtocolError("A change set must contain at least one operation.")
        if len(raw_operations) > MAX_OPERATIONS:
            raise ProtocolError(f"A change set may contain at most {MAX_OPERATIONS} operations.")
        operations = [self._operation(item, index) for index, item in enumerate(raw_operations, start=1)]
        self._validate_operation_dependencies(operations)
        requested_risk = str(data.get("risk", "MEDIUM")).upper()
        risk = requested_risk if requested_risk in {"LOW", "MEDIUM", "HIGH"} else "MEDIUM"
        if any(operation.kind in HIGH_RISK_KINDS or operation.payload.get("overwrite") is True for operation in operations):
            risk = "HIGH"
        validation_data = data.get("validation") if isinstance(data.get("validation"), dict) else {}
        validation = ValidationSpec(
            compile=bool(validation_data.get("compile", True)),
            playMode=bool(validation_data.get("playMode", False)),
            checks=self._strings(validation_data.get("checks", [])),
        )
        summary = str(data.get("summary", "")).strip() or (answer[:160] if response_type == "answer" else "")
        if not summary:
            raise ProtocolError("Change-set summary is required.")
        return ChangeSet(
            requestId=self._safe_id(data.get("requestId")),
            summary=summary,
            risk=risk,
            requiresConfirmation=bool(data.get("requiresConfirmation", risk != "LOW")),
            operations=operations,
            validation=validation,
            explanation=self._strings(data.get("explanation", [])),
            warnings=self._strings(data.get("warnings", [])) + normalization_warnings,
            model=model or str(data.get("model", "")),
            responseType=response_type,
            answer=answer,
        )

    def salvage_complete_answer(self, response: str, model: str = "") -> ChangeSet | None:
        """Recover only a fully closed answer string from truncated trailing JSON.

        Mutation manifests are never salvaged because partial operations are unsafe.
        """
        if not isinstance(response, str) or '"responseType"' not in response or '"answer"' not in response:
            return None
        if not re.search(r'"responseType"\s*:\s*"answer"', response, re.IGNORECASE):
            return None
        match = re.search(r'"answer"\s*:\s*', response)
        if not match:
            return None
        try:
            answer, _ = json.JSONDecoder().raw_decode(response[match.end():])
        except json.JSONDecodeError:
            return None
        if not isinstance(answer, str) or not answer.strip():
            return None
        return ChangeSet(
            requestId=self._safe_id(None), summary=answer.strip()[:160], risk="LOW",
            requiresConfirmation=False, operations=[],
            validation=ValidationSpec(compile=False, playMode=False, checks=[]),
            explanation=[], warnings=["Model JSON tail was truncated; the complete answer text was recovered safely."],
            model=model, responseType="answer", answer=answer.strip(),
        )

    def salvage_complete_change_set(self, response: str, model: str = "") -> ChangeSet | None:
        """Recover a manifest only when its complete operations array is closed."""
        if not isinstance(response, str) or not re.search(r'"responseType"\s*:\s*"change_set"', response, re.IGNORECASE):
            return None
        operations = self._closed_json_value(response, "operations")
        if not isinstance(operations, list) or not operations:
            return None
        summary = self._closed_json_value(response, "summary")
        if not isinstance(summary, str) or not summary.strip():
            return None
        risk = self._closed_json_value(response, "risk")
        confirmation = self._closed_json_value(response, "requiresConfirmation")
        validation = self._closed_json_value(response, "validation")
        data = {
            "protocol": PROTOCOL, "responseType": "change_set", "requestId": "",
            "summary": summary, "answer": "", "risk": risk if isinstance(risk, str) else "MEDIUM",
            "requiresConfirmation": confirmation if isinstance(confirmation, bool) else True,
            "operations": operations,
            "validation": validation if isinstance(validation, dict) else {"compile": True, "playMode": False, "checks": []},
            "explanation": [],
            "warnings": ["Model JSON tail was truncated after a complete operation manifest; trailing prose was omitted."],
        }
        try:
            return self.parse(data, model=model)
        except ProtocolError:
            return None

    @staticmethod
    def _closed_json_value(response: str, key: str):
        match = re.search(r'"' + re.escape(key) + r'"\s*:\s*', response)
        if not match:
            return None
        try:
            value, _ = json.JSONDecoder().raw_decode(response[match.end():])
            return value
        except json.JSONDecodeError:
            return None

    def _operation(self, value: Any, index: int) -> ChangeOperation:
        if not isinstance(value, dict):
            raise ProtocolError(f"Operation {index} must be an object.")
        kind = str(value.get("kind", "")).strip()
        if kind not in ALLOWED_KINDS:
            raise ProtocolError(f"Operation {index} has unsupported kind '{kind}'.")
        payload = {key: item for key, item in value.items() if key not in {"id", "kind"}}
        for field_name in PATH_FIELDS:
            if payload.get(field_name):
                payload[field_name] = self.safe_asset_path(payload[field_name])
        if kind == "write_text":
            self._require(payload, index, "path", "content")
            if self._is_unity_serialized_asset(payload["path"]):
                raise ProtocolError(f"Operation {index} must use a Unity operation instead of writing serialized asset YAML: {payload['path']}")
            if len(str(payload["content"])) > MAX_TEXT_SIZE:
                raise ProtocolError(f"Operation {index} text content is too large.")
        elif kind == "replace_text":
            self._require(payload, index, "path", "search", "replacement")
            if self._is_unity_serialized_asset(payload["path"]):
                raise ProtocolError(f"Operation {index} must use a Unity operation instead of editing serialized asset YAML: {payload['path']}")
            if not str(payload["search"]):
                raise ProtocolError(f"Operation {index} search text cannot be empty.")
        elif kind in {"delete_asset", "create_folder", "create_scene"}:
            self._require(payload, index, "path")
        elif kind == "create_game_object":
            self._require(payload, index, "name")
        elif kind in {"add_component", "set_property"}:
            self._require(payload, index, "targetPath")
            target = str(payload["targetPath"]).replace("\\", "/").casefold()
            if target.endswith((".unity", ".prefab", ".mat", ".asset", ".cs", ".shader", ".json")) or target.startswith("assets/"):
                raise ProtocolError(f"Operation {index} targetPath must be a scene GameObject path, not an asset file: {payload['targetPath']}")
            if kind == "add_component":
                self._require(payload, index, "component")
            else:
                self._require(payload, index, "property")
        elif kind == "create_prefab":
            self._require(payload, index, "assetPath", "name")
        elif kind == "instantiate_prefab":
            self._require(payload, index, "assetPath")
        elif kind == "create_material":
            self._require(payload, index, "assetPath")
        elif kind == "create_effect":
            self._require(payload, index, "name")
        elif kind == "create_ui_screen":
            self._require(payload, index, "name", "title")
            if payload.get("sourceImagePath"):
                payload["sourceImagePath"] = self.safe_asset_path(payload["sourceImagePath"])
            asset_path = str(payload.get("assetPath", "")).replace("\\", "/")
            if asset_path.casefold().endswith(".unity"):
                payload.setdefault("scenePath", asset_path)
                payload["assetPath"] = ""
            elif asset_path and not asset_path.casefold().endswith(".prefab"):
                raise ProtocolError(f"Operation {index} create_ui_screen assetPath must end in .prefab: {asset_path}")
            scene_path = str(payload.get("scenePath", "")).replace("\\", "/")
            if scene_path and not scene_path.casefold().endswith(".unity"):
                raise ProtocolError(f"Operation {index} create_ui_screen scenePath must end in .unity: {scene_path}")
            # Models sometimes identify a scene asset as a gameplay "target".
            # Preserve the intent but route it to the runtime scene-loading field.
            if str(payload.get("gameplayTarget", "")).replace("\\", "/").casefold().endswith(".unity"):
                payload.setdefault("gameplayScenePath", payload["gameplayTarget"])
                payload["gameplayTarget"] = ""
            for field_name, allowed_values in {
                "referenceLayout": {"rebuild", "background", "hero"},
                "imageFit": {"contain", "cover"},
                "ctaAnchor": {"top_left", "top_center", "top_right", "center_left", "center", "center_right", "bottom_left", "bottom_center", "bottom_right"},
            }.items():
                layout_value = str(payload.get(field_name, "")).strip().casefold()
                if layout_value and layout_value not in allowed_values:
                    raise ProtocolError(f"Operation {index} {field_name} has an unsupported value: {layout_value}")
                if layout_value:
                    payload[field_name] = layout_value
        elif kind == "build_character":
            self._require(payload, index, "name", "sourceImagePath", "dimension")
        elif kind == "generate_prototype":
            self._require(payload, index, "gameKey", "name")
        return ChangeOperation(self._safe_id(value.get("id"), prefix=f"op{index}"), kind, payload)

    @staticmethod
    def _is_unity_serialized_asset(path: Any) -> bool:
        return posixpath.splitext(str(path).replace("\\", "/"))[1].casefold() in UNITY_SERIALIZED_EXTENSIONS

    @staticmethod
    def _normalise_ui_operations(raw_operations: Any) -> tuple[Any, list[str]]:
        """Remove only impossible duplicate UI child edits from a generated UI plan.

        create_ui_screen owns its Canvas, Button and button action. A model may still
        append add_component/set_property against a .unity/.prefab asset path, but an
        asset file is not a scene GameObject and Unity cannot apply that operation.
        Keep strict rejection for every non-UI plan.
        """
        if not isinstance(raw_operations, list):
            return raw_operations, []
        has_ui_screen = any(isinstance(item, dict) and item.get("kind") == "create_ui_screen" for item in raw_operations)
        if not has_ui_screen:
            return raw_operations, []
        ui_operations = [item for item in raw_operations if isinstance(item, dict) and item.get("kind") == "create_ui_screen"]
        primary_ui = ui_operations[0] if ui_operations else None
        ui_names = {
            ChangeSetParser._normalise_ui_name(primary_ui.get(field, ""))
            for field in ("name", "title")
        } if primary_ui else set()
        ui_names.discard("")
        retained, omitted, merged = [], 0, 0
        for item in raw_operations:
            target = str(item.get("targetPath", "")).replace("\\", "/").casefold() if isinstance(item, dict) else ""
            impossible_asset_target = target.endswith((".unity", ".prefab", ".mat", ".asset"))
            if isinstance(item, dict) and item.get("kind") in {"add_component", "set_property"} and impossible_asset_target:
                omitted += 1
                continue
            if isinstance(item, dict) and primary_ui is not None and item is not primary_ui and item.get("kind") in {"create_scene", "create_prefab", "create_material"}:
                candidate = str(item.get("name", "") or item.get("assetPath", "") or item.get("path", ""))
                base_name = ChangeSetParser._normalise_ui_name(posixpath.splitext(posixpath.basename(candidate.replace("\\", "/")))[0])
                related = bool(base_name and any(base_name in ui_name or ui_name in base_name for ui_name in ui_names))
                if related:
                    if item.get("kind") == "create_prefab" and not primary_ui.get("assetPath"):
                        prefab_path = str(item.get("assetPath", ""))
                        if prefab_path.casefold().endswith(".prefab"):
                            primary_ui["assetPath"] = prefab_path
                    elif item.get("kind") == "create_scene" and not primary_ui.get("scenePath") and not primary_ui.get("assetPath"):
                        scene_path = str(item.get("path", ""))
                        if scene_path.casefold().endswith(".unity"):
                            primary_ui["scenePath"] = scene_path
                    omitted += 1
                    merged += 1
                    continue
            retained.append(item)
        warning = []
        if omitted:
            warning.append("UI operation was simplified because create_ui_screen creates its own controls and related UI assets.")
        return retained, warning

    @staticmethod
    def _normalise_ui_name(value: Any) -> str:
        text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
        return re.sub(r"[^a-z0-9]+", "", text.casefold())

    @staticmethod
    def _validate_operation_dependencies(operations: list[ChangeOperation]) -> None:
        """A generated UI prefab has no scene child path until Unity creates it."""
        generated_ui_roots = {
            str(operation.payload.get("name", "")).strip()
            for operation in operations
            if operation.kind == "create_ui_screen" and str(operation.payload.get("name", "")).strip()
        }
        for operation in operations:
            if operation.kind not in {"add_component", "set_property"}:
                continue
            target = str(operation.payload.get("targetPath", "")).strip()
            if any(target == root or target.startswith(root + "/") for root in generated_ui_roots):
                raise ProtocolError(
                    f"Operation '{operation.kind}' targets a child of newly created UI '{target}'. "
                    "Configure create_ui_screen directly instead."
                )

    @staticmethod
    def safe_asset_path(value: Any) -> str:
        path = str(value).strip().replace("\\", "/")
        if not path or path.startswith(("/", "~")) or re.match(r"^[A-Za-z]:", path):
            raise ProtocolError(f"Asset path must be project-relative: {value}")
        normalized = posixpath.normpath(path)
        if normalized == "Assets" or not normalized.startswith("Assets/") or normalized.startswith("../"):
            raise ProtocolError(f"Asset path escapes the Unity Assets folder: {value}")
        # Older templates wrote generated content under the installed package.
        # That package is immutable for autonomous jobs, so keep generated game
        # and character output in the editable project-owned area instead.
        legacy_generated_roots = (
            ("Assets/AIEngineer/GeneratedGames/", "Assets/AIEngineerGenerated/Games/"),
            ("Assets/AIEngineer/GeneratedCharacters/", "Assets/AIEngineerGenerated/Characters/"),
        )
        for legacy_root, generated_root in legacy_generated_roots:
            if normalized.casefold().startswith(legacy_root.casefold()):
                return generated_root + normalized[len(legacy_root):]
        return normalized

    @staticmethod
    def _as_object(response: str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(response, dict):
            return response
        if not isinstance(response, str) or not response.strip():
            raise ProtocolError("Model returned an empty response.")
        text = response.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE | re.DOTALL).strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            start, end = text.find("{"), text.rfind("}")
            if start < 0 or end <= start:
                raise ProtocolError("Model response does not contain a JSON object.")
            try:
                data = json.loads(text[start : end + 1])
            except json.JSONDecodeError as error:
                raise ProtocolError(f"Model response is not valid JSON: {error.msg}") from error
        if not isinstance(data, dict):
            raise ProtocolError("Model response must be a JSON object.")
        return data

    @staticmethod
    def _require(payload: dict[str, Any], index: int, *fields: str) -> None:
        missing = [name for name in fields if name not in payload or payload[name] is None or str(payload[name]).strip() == ""]
        if missing:
            raise ProtocolError(f"Operation {index} is missing: {', '.join(missing)}")

    @staticmethod
    def _safe_id(value: Any, prefix: str = "job") -> str:
        candidate = re.sub(r"[^A-Za-z0-9_-]", "", str(value or ""))[:64]
        return candidate or f"{prefix}-{uuid4().hex[:12]}"

    @staticmethod
    def _strings(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]
