"""Build a bounded Unity context for local planning without dumping the project."""

from __future__ import annotations

import json
from pathlib import Path
import re
import unicodedata
from typing import Any

from Source.Knowledge.document_knowledge import DocumentKnowledge


class UnityProjectContext:
    MAX_FILES = 6
    MAX_FILE_CHARS = 8_000
    MAX_TOTAL_SCRIPT_CHARS = 40_000
    MAX_SCENE_OBJECTS = 120
    MAX_DOCUMENTS = 4
    MAX_DOCUMENT_CHARS = 5_000
    MAX_TOTAL_DOCUMENT_CHARS = 16_000

    def __init__(self, external_documents=None):
        self.external_documents = external_documents or DocumentKnowledge()

    def build(self, project_root: str | Path, request: dict[str, Any], prompt: str) -> dict[str, Any]:
        root = Path(project_root).resolve()
        if not (root / "Assets").is_dir() or not (root / "ProjectSettings").is_dir():
            raise ValueError(f"Not a Unity project: {root}")
        project = request.get("project") if isinstance(request.get("project"), dict) else {}
        objects = request.get("objects") if isinstance(request.get("objects"), list) else []
        return {
            "project_root": str(root),
            "unity_version": self._unity_version(root),
            "render_pipeline": self._render_pipeline(root),
            "active_scene": str(request.get("activeScene", "")),
            "target_orientation": str(request.get("targetOrientation", "unknown")),
            "requested_language": str(request.get("language", "Turkish")),
            "scene_objects": objects[: self.MAX_SCENE_OBJECTS],
            "assets": {key: list(project.get(key, []))[:150] for key in ("scenes", "prefabs", "materials", "textures", "audio", "scripts", "animations")},
            "relevant_scripts": self._relevant_scripts(root, prompt, request),
            "script_api": self._script_api(root, prompt),
            "unity_documentation": self._relevant_unity_documentation(root, str(request.get("documentationQuery") or prompt)),
        }

    @staticmethod
    def as_prompt(context: dict[str, Any]) -> str:
        return json.dumps(context, ensure_ascii=False, indent=2)

    def _relevant_scripts(self, root: Path, prompt: str, request: dict[str, Any]) -> list[dict[str, object]]:
        tokens = self._tokens(prompt)
        selected = request.get("selectedAssets")
        explicit_paths = {str(path).replace("\\", "/") for path in selected if str(path).endswith(".cs")} if isinstance(selected, list) else set()
        candidates = []
        for path in (root / "Assets").rglob("*.cs"):
            relative = path.relative_to(root).as_posix()
            if "/AIEngineer/" in f"/{relative}" and relative not in explicit_paths:
                continue
            try:
                content = path.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeError):
                continue
            haystack = self._normalise(f"{relative} {path.stem} {content[:50_000]}")
            score = 100 if relative in explicit_paths else 0
            score += sum(4 if token in self._normalise(path.stem) else min(haystack.count(token), 3) for token in tokens)
            candidates.append((score, relative, content))
        candidates.sort(key=lambda item: (-item[0], item[1].casefold()))
        chosen = [item for item in candidates if item[0] > 0][: self.MAX_FILES]
        if not chosen:
            chosen = candidates[: min(5, self.MAX_FILES)]
        result, remaining = [], self.MAX_TOTAL_SCRIPT_CHARS
        for _, relative, content in chosen:
            limit = min(self.MAX_FILE_CHARS, remaining)
            if limit <= 0: break
            result.append({"path": relative, "content": content[:limit], "truncated": len(content) > limit})
            remaining -= limit
        return result

    def _relevant_unity_documentation(self, root: Path, prompt: str) -> list[dict[str, object]]:
        """Supply a small, relevant subset of installed/project Unity package documentation."""
        tokens = self._tokens(prompt)
        candidates: list[tuple[int, str, str]] = []
        documentation_roots = [root / "Assets", root / "Packages"]
        package_cache = root / "Library" / "PackageCache"
        if package_cache.is_dir():
            documentation_roots.extend(path for path in package_cache.glob("*/Documentation~") if path.is_dir())
        for documentation_root in documentation_roots:
            if not documentation_root.is_dir():
                continue
            for path in documentation_root.rglob("*"):
                if not path.is_file() or path.suffix.casefold() not in {".md", ".txt"}:
                    continue
                try:
                    content = path.read_text(encoding="utf-8-sig")
                except (OSError, UnicodeError):
                    continue
                relative = path.relative_to(root).as_posix() if root in path.parents else str(path)
                normalised = self._normalise(f"{relative} {content[:30_000]}")
                score = sum(min(normalised.count(token), 4) for token in tokens)
                if "documentation~" in relative.casefold() or "readme" in path.name.casefold():
                    score += 2
                # Project/package documentation is closest to the actual installed
                # environment and therefore outranks the global Unity archive.
                candidates.append((200 + score, relative, content))
        try:
            for document in self.external_documents.get_document(prompt, limit=self.MAX_DOCUMENTS, max_paragraphs=6, max_code_blocks=3):
                content = "\n\n".join([
                    *[str(item) for item in document.get("paragraphs", [])],
                    *[str(item) for item in document.get("code_blocks", [])],
                ])
                if content:
                    candidates.append((100, str(document.get("path", "")), content))
        except (OSError, UnicodeError, ValueError):
            pass
        candidates.sort(key=lambda item: (-item[0], item[1].casefold()))
        chosen = [item for item in candidates if item[0] > 0][: self.MAX_DOCUMENTS]
        if not chosen:
            chosen = candidates[: self.MAX_DOCUMENTS]
        result, remaining = [], self.MAX_TOTAL_DOCUMENT_CHARS
        for _, relative, content in chosen:
            limit = min(self.MAX_DOCUMENT_CHARS, remaining)
            if limit <= 0:
                break
            result.append({"path": relative, "content": content[:limit], "truncated": len(content) > limit})
            remaining -= limit
        return result

    def _script_api(self, root: Path, prompt: str) -> list[dict[str, object]]:
        """Expose real public script contracts without spending the model budget on whole files."""
        tokens = self._tokens(prompt)
        candidates: list[tuple[int, dict[str, object]]] = []
        for path in (root / "Assets").rglob("*.cs"):
            relative = path.relative_to(root).as_posix()
            if "/AIEngineer/" in f"/{relative}":
                continue
            try:
                content = path.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeError):
                continue
            class_match = re.search(r"\b(?:public\s+)?class\s+(\w+)", content)
            if not class_match:
                continue
            class_name = class_match.group(1)
            methods = re.findall(r"\bpublic\s+(?:static\s+)?[\w<>\[\], ]+\s+(\w+)\s*\(", content)
            fields = re.findall(r"\bpublic\s+(?:static\s+)?[\w<>\[\], ]+\s+(\w+)\s*(?:=|;|\{)", content)
            normalised = self._normalise(f"{relative} {class_name} {' '.join(methods)} {' '.join(fields)}")
            score = sum(5 if token in self._normalise(class_name) else min(normalised.count(token), 3) for token in tokens)
            if score <= 0:
                continue
            candidates.append((score, {"path": relative, "class": class_name, "public_methods": sorted(set(methods))[:24], "public_fields": sorted(set(fields))[:32]}))
        candidates.sort(key=lambda item: (-item[0], str(item[1]["class"]).casefold()))
        return [item[1] for item in candidates[:12]]

    @staticmethod
    def _unity_version(root: Path) -> str:
        version_file = root / "ProjectSettings" / "ProjectVersion.txt"
        if not version_file.is_file():
            return "unknown"
        match = re.search(r"m_EditorVersion:\s*(.+)", version_file.read_text(encoding="utf-8-sig"))
        return match.group(1).strip() if match else "unknown"

    @staticmethod
    def _render_pipeline(root: Path) -> str:
        manifest = root / "Packages" / "manifest.json"
        text = manifest.read_text(encoding="utf-8-sig") if manifest.is_file() else ""
        if "com.unity.render-pipelines.high-definition" in text:
            return "HDRP"
        if "com.unity.render-pipelines.universal" in text:
            return "URP"
        return "BuiltIn"

    @classmethod
    def _tokens(cls, value: str) -> set[str]:
        stop = {"bir", "ve", "ile", "icin", "ekle", "olustur", "yap", "the", "and", "for", "add", "create", "unity"}
        tokens = {token for token in re.findall(r"[a-z0-9_]+", cls._normalise(value)) if len(token) > 2 and token not in stop}
        aliases = {
            "top": {"ball", "marble"}, "toplar": {"ball", "marble"},
            "zincir": {"chain"}, "bomba": {"bomb", "explosion"},
            "patlama": {"explode", "explosion", "destroy"}, "patlat": {"explode", "explosion", "destroy"},
            "puan": {"score"}, "efekt": {"effect", "particle"},
            "ses": {"audio", "sound"}, "mermi": {"projectile", "shot"},
            "atis": {"shot", "shooter"}, "oyun": {"game"},
        }
        expanded = set(tokens)
        for token in tokens:
            expanded.update(aliases.get(token, ()))
        return expanded

    @staticmethod
    def _normalise(value: str) -> str:
        table = str.maketrans({"ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g", "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c"})
        return unicodedata.normalize("NFKD", str(value).translate(table)).encode("ascii", "ignore").decode("ascii").casefold()
