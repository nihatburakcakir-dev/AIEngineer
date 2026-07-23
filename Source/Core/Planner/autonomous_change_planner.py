"""Local-first planner that emits executable Unity change sets."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from Source.Core.Config.config_manager import ConfigManager
from Source.Core.Executor.compiler_quick_fixer import CompilerQuickFixer
from Source.Core.Knowledge.unity_project_context import UnityProjectContext
from Source.Core.Models.change_protocol import ChangeSet, ChangeSetParser, ProtocolError
from Source.LLM.llm_client import LocalLLMRouter
from Source.LLM.vision_router import OptionalVisionRouter


SYSTEM_PROMPT = """You are the planning and code-generation engine inside a Unity Editor tool.
Return JSON only. Never say that a change was applied; Unity applies it after validation.
Use protocol ai-engineer.change-set/v1 and only these operation kinds:
write_text, replace_text, delete_asset, create_folder, create_scene, create_game_object,
add_component, set_property, create_prefab, instantiate_prefab, create_material,
create_effect, create_ui_screen, build_character, generate_prototype, save_scene.
generate_image is available for a new PNG under Assets/AIEngineerGenerated only. It requires prompt, outputPath, width and height; set importType to Sprite or Default.

This is a single-request orchestration system: a planning specialist has already decomposed the user intent, you are the code/Unity specialist, and Unity dispatches generate_image operations to Flux.2 automatically. Do not ask the user to choose a model or press a second tool button. Keep every needed artifact in one change set.

Decide the user's intent from meaning and project context, not from hard-coded keywords.
For a question, explanation, analysis, or recommendation that does not explicitly request a project mutation, return:
{"protocol":"ai-engineer.change-set/v1","responseType":"answer","requestId":"","summary":"","answer":"grounded answer","risk":"LOW","requiresConfirmation":false,"operations":[],"validation":{"compile":false,"playMode":false,"checks":[]},"explanation":[],"warnings":[]}
For a requested Unity action or project mutation, return:
{"protocol":"ai-engineer.change-set/v1","responseType":"change_set","requestId":"","summary":"","answer":"","risk":"LOW|MEDIUM|HIGH","requiresConfirmation":true,
 "operations":[{"id":"op1","kind":"write_text","path":"Assets/...","content":"complete file content","overwrite":false}],
 "validation":{"compile":true,"playMode":false,"checks":[""]},"explanation":[""],"warnings":[""]}

Rules:
- All asset/file paths are project-relative and start with Assets/. Never use absolute paths or ..
- Prefer new adapter/controller scripts under Assets/AIEngineerGenerated/ over modifying unrelated user scripts.
- For an existing script change use replace_text only when the exact search text is present in supplied context; otherwise write a complete new script.
- Never use write_text or replace_text for .prefab, .unity, .mat, .asset or .controller files and never emit Unity YAML. These files must be created or changed through create_prefab, create_ui_screen, create_scene, create_material or the appropriate Unity operation.
- C# must compile in the reported Unity version and pipeline. Use Unity APIs, no invented types, no UnityEditor namespace in runtime scripts.
- Use supplied Unity/package documentation excerpts as project-specific technical evidence. Prefer documented Unity APIs and project packages over guesses.
- Understand ordinary Turkish and English Unity requests semantically. Words such as button, fit to screen, landscape, prefab, effect, fix and analyze are normal concepts, not special commands.
- Use requested_language from the supplied Unity context for every user-visible field: answer, summary, explanation, warnings and validation.checks. This is mandatory: when requested_language is Turkish, do not write these fields in English. Code identifiers, asset paths and Unity API names are the only exceptions. Check units, screen orientation, API names and numeric examples for internal consistency.
- Keep answer responses concise (normally under 500 words). Keep change sets to the smallest complete implementation.
- Inspect active_scene, target_orientation, scene_objects, selected assets, installed packages, scripts and visual evidence before deciding what to answer or change.
- When a reference image is supplied, reconstruct its editable Unity structure. Do not paste the complete image as a single RawImage unless the user explicitly asks for a static image-only screen.
- Visible interactive controls must become real Unity controls. A start/play CTA must have a runtime action that reveals gameplay already in the active scene or loads an explicitly requested scene.
- create_game_object supports name, parentPath, primitive, position, rotation, scale and components.
- components is an array of {"type":"Unity component type","properties":[{"name":"serialized field","type":"string|float|int|bool|color|vector2|vector3|object","value":"..."}]}.
- add_component and set_property targetPath always refer to an actual Hierarchy GameObject path (for example "ZumaGameManager" or "Canvas/StartButton"), never an Assets path, C# file, prefab, material or scene file. set_property must include component for every non-Transform field, plus valueType and value (or objectPath for an asset/GameObject reference). To change code, use write_text for a new complete C# file or replace_text with an exact existing snippet. script_api is the authoritative compact list of public methods and fields in the current project: do not call an API absent from it. If required behavior is missing, generate a concise adapter script using documented Unity APIs and attach it to a real GameObject.
- create_prefab supports assetPath, name, primitive and components. create_effect supports name, assetPath optional, color, duration, startSpeed, startSize, maxParticles and shape.
- create_ui_screen creates a mobile-first game entrance UI. It requires name and title and accepts subtitle, buttonLabel, theme, highlights (up to three short player-facing feature strings), color, sourceImagePath (an optional Assets image), assetPath (prefab path ending in .prefab), scenePath (scene path ending in .unity), orientation (landscape or portrait), gameplayTarget (a real existing scene object to reveal), gameplayScenePath and pulseAccent. It also accepts referenceLayout (rebuild|background|hero), imageFit (contain|cover), ctaAnchor (top_left|top_center|top_right|center_left|center|center_right|bottom_left|bottom_center|bottom_right), and replaceExisting. When a reference image exists, decide these three layout fields from visual evidence: rebuild makes editable Unity UI from the visual hierarchy; background keeps complex rendered artwork as a fitted background and overlays editable controls; hero uses it as a fitted hero panel. Choose background for a detailed illustrated/game-art reference when the vision model cannot reliably identify every visual layer; choose rebuild only for a simple, clearly segmented interface whose pieces can be recreated. Set ctaAnchor to the visible start/play CTA position detected by vision, never a guessed default when visual evidence is available. If the user asks to fix, revise or replace an existing generated menu, set replaceExisting true and reuse the actual existing root name from scene_objects. Use it whenever the request is for a new game, prototype, title screen, start menu or mobile UI. Its title, subtitle and highlights must clearly communicate the game theme, objective and primary player action; choose a color that fits the requested theme. Respect target_orientation. For a start CTA, set gameplayTarget when a gameplay root exists; set pulseAccent when the request asks for a glow/pulse effect. Never put a .unity path in assetPath: use scenePath.
- gameplayScenePath must exactly match an entry in assets.scenes. Never invent a scene path. For a reusable UI prefab that should open the current game, prefer active_scene when it is one of the listed scenes unless the user names another gameplay scene.
- create_ui_screen already creates its Canvas, real Button action, orientation layout and optional pulseAccent. Use one create_ui_screen with an assetPath ending in .prefab for a requested reusable entrance UI prefab; do not use create_prefab plus add_component to reconstruct an entrance UI. Do not add_component or set_property against a child of a create_ui_screen created in the same change set; that child does not exist until Unity executes the UI operation. Do not create a duplicate standalone effect when pulseAccent handles the requested UI glow.
- For a gameplay feature request (for example bombs, chain reactions, scoring, projectile impacts, power-ups, enemies or UI actions), inspect relevant_scripts and unity_documentation before planning. Include the complete runtime behavior, not only a visual placeholder: create or update a concise runtime C# script under Assets/AIEngineerGenerated/Scripts when the current scripts do not expose the requested behavior; then attach/wire it to real existing scene objects and add any required prefab/effect operations. A visual effect alone is never a complete gameplay feature. Keep each generated script focused and compilable so the plan stays within the response budget.
- Decompose every gameplay feature into four responsibilities and implement every applicable one: (1) core behavior, (2) spawning/distribution/triggering, (3) visual/audio feedback, and (4) integration with existing gameplay state such as chain lists, health or score. Do not put an omitted responsibility in warnings. For random insertion into an existing collection, create a controller/adapter attached to the real manager or spawner and use UnityEngine.Random.Range with the real public collection/API from script_api. A behavior component that is never spawned, attached or triggered is incomplete.
- When a supplied reference image and user request describe a title/start UI with a playable CTA, produce exactly one create_ui_screen operation unless the user explicitly requests separate unrelated assets. Put the requested prefab path, sourceImagePath, orientation, gameplay target and pulseAccent on that operation. Do not split this work into create_scene, create_prefab, create_material or add_component operations.
- build_character supports name, dimension (2D or 3D), sourceImagePath and optional prefabPath.
- generate_prototype supports gameKey, name, scenePath and systems. Use it for a complete known prototype, then add any requested custom scripts/objects as later operations.
- Destructive operations are HIGH risk. Set overwrite true only when intentionally replacing an existing file.
- Include compile validation for code and playMode validation for gameplay changes.
- Keep the plan bounded to the smallest complete set of operations (maximum 48).
"""


class AutonomousChangePlanner:
    def __init__(self, config=None, router=None, context_builder=None, vision_router=None, retries=2):
        self.config = config or ConfigManager()
        self.router = router or LocalLLMRouter(self.config)
        self.context_builder = context_builder or UnityProjectContext()
        self.vision_router = vision_router or OptionalVisionRouter(self.config)
        self.parser = ChangeSetParser()
        self.quick_fixer = CompilerQuickFixer()
        self.retries = retries

    def plan(self, request: dict[str, Any]) -> ChangeSet:
        prompt = str(request.get("prompt", "")).strip()
        if not prompt:
            raise ValueError("Prompt is required.")
        project_root = request.get("projectPath") or self.config.project_root
        context = self.context_builder.build(project_root, request, prompt)
        context["reference_image_path"] = str(request.get("imagePath", ""))
        image_path = str(request.get("imagePath", "")).strip()
        vision_mode = str(request.get("visionMode", request.get("modelMode", "local")))
        visual_path = Path(project_root) / image_path if image_path.startswith("Assets/") else Path(image_path)
        visual = self._visual_context(str(visual_path), vision_mode) if image_path else None
        mode = str(request.get("modelMode", "local"))
        feature_blueprint = self._orchestration_brief(prompt, context, mode)
        return self._generate_and_parse(
            self._planning_prompt(prompt, context, visual, feature_blueprint),
            mode,
            validator=lambda change_set: self._validate_project_grounding(change_set, context, prompt),
        )

    def repair(self, request: dict[str, Any]) -> ChangeSet:
        prompt = str(request.get("prompt", "")).strip()
        project_root = request.get("projectPath") or self.config.project_root
        previous = request.get("changeSet") if isinstance(request.get("changeSet"), dict) else {}
        diagnostics = request.get("diagnostics") if isinstance(request.get("diagnostics"), list) else []
        quick_repair = self.quick_fixer.try_repair(previous, diagnostics)
        if quick_repair is not None:
            change_set = self.parser.parse(quick_repair, model="compiler-rule-engine")
            self._validate_repair_scope(previous, change_set)
            return change_set
        touched_paths = self._operation_paths(previous)
        context = self._repair_context(project_root, request, touched_paths)
        repair_prompt = f"""Repair the previous Unity change set. Return a complete replacement change set, JSON only.
Original user request:
{prompt}

STRICT REPAIR SCOPE:
- You may only write/replace these original paths: {json.dumps(touched_paths, ensure_ascii=False)}
- Preserve every non-file operation from the previous set (same object/prefab/effect target).
- Do not create or modify unrelated scripts, classes, assets or systems.
- Fix only the supplied compiler/validation diagnostics.
- Prefabs, scenes, materials and controllers are Unity-managed assets: never repair them with write_text, replace_text or YAML. Re-emit the original create_prefab/create_ui_screen/create_scene/create_material operation with corrected parameters instead.

Compiler/validation diagnostics:
{json.dumps(diagnostics, ensure_ascii=False, indent=2)}

Previous change set:
{json.dumps(previous, ensure_ascii=False, indent=2)}

Current bounded Unity context:
{self.context_builder.as_prompt(context)}

Fix the actual cause. Do not repeat an operation that diagnostics prove invalid. Preserve working requested behavior."""
        return self._generate_and_parse(
            repair_prompt,
            str(request.get("modelMode", "local")),
            validator=lambda change_set: self._validate_repair_scope(previous, change_set),
        )

    def _generate_and_parse(self, prompt: str, mode: str, validator=None) -> ChangeSet:
        if mode not in {"local", "qwen_code", "codex", "cloud"}:
            raise ValueError("Model mode must be local, qwen_code, codex or cloud.")
        current_prompt = prompt
        last_error = None
        if mode == "local":
            model = self.config.model_for("code_generation")
        elif mode == "qwen_code":
            model = "qwen-code/" + self.config.qwen_code_model
        elif mode == "codex":
            model = "codex-cli/" + (self.config.codex_model or "chatgpt-default")
        else:
            model = self.config.cloud_model_for("code_generation")
        for attempt in range(self.retries + 1):
            response = self.router.generate(current_prompt, task="code_generation", system=SYSTEM_PROMPT, mode=mode)
            try:
                change_set = self.parser.parse(response, model=model)
                if validator is not None:
                    validator(change_set)
                return change_set
            except ProtocolError as error:
                last_error = error
                salvaged = self.parser.salvage_complete_answer(response, model=model)
                if salvaged is not None:
                    try:
                        if validator is not None:
                            validator(salvaged)
                        return salvaged
                    except ProtocolError as salvage_error:
                        last_error = salvage_error
                salvaged = self.parser.salvage_complete_change_set(response, model=model)
                if salvaged is not None:
                    try:
                        if validator is not None:
                            validator(salvaged)
                        return salvaged
                    except ProtocolError as salvage_error:
                        last_error = salvage_error
                if attempt >= self.retries:
                    preview = " ".join(str(response)[:600].split())
                    raise ProtocolError(f"{error} Model output preview: {preview}") from error
                current_prompt = f"""Your previous response failed protocol/project validation:
{error}

Return a newly reasoned COMPLETE JSON change set only. Do not use Markdown and do not copy or repeat the invalid implementation. Use only the real APIs, scene targets and assets listed in the original context. If a required project API is absent, implement the behavior inside a new adapter using available public fields and documented Unity APIs.

Original task and context:
{prompt}"""
        raise last_error or ProtocolError("Change set generation failed.")

    def _repair_context(self, project_root: str, request: dict[str, Any], paths: list[str]) -> dict[str, Any]:
        root = Path(project_root).resolve()
        files = []
        for asset_path in paths:
            try:
                safe_path = self.parser.safe_asset_path(asset_path)
                full_path = (root / safe_path).resolve()
                if root not in full_path.parents or not full_path.is_file():
                    continue
                files.append({"path": safe_path, "content": full_path.read_text(encoding="utf-8-sig")[:16_000]})
            except (OSError, UnicodeError, ProtocolError):
                continue
        return {
            "project_root": str(root),
            "active_scene": str(request.get("activeScene", "")),
            "repair_scope_files": files,
        }

    @staticmethod
    def _operation_paths(change_set: dict[str, Any]) -> list[str]:
        paths = []
        for operation in change_set.get("operations", []) if isinstance(change_set.get("operations"), list) else []:
            if not isinstance(operation, dict):
                continue
            for field_name in ("path", "assetPath", "scenePath"):
                value = str(operation.get(field_name, "")).strip().replace("\\", "/")
                if value and value not in paths:
                    paths.append(value)
        return paths

    def _validate_repair_scope(self, previous: dict[str, Any], repaired: ChangeSet) -> None:
        previous_operations = previous.get("operations", []) if isinstance(previous.get("operations"), list) else []
        allowed_paths = set(self._operation_paths(previous))
        repaired_paths = set()
        if len(repaired.operations) > len(previous_operations) + 2:
            raise ProtocolError("Repair expanded beyond the original operation count.")
        for operation in repaired.operations:
            if operation.kind == "delete_asset":
                raise ProtocolError("A repair plan may not introduce deletion.")
            for field_name in ("path", "assetPath", "scenePath"):
                value = str(operation.payload.get(field_name, "")).strip()
                if not value:
                    continue
                repaired_paths.add(value)
                if value not in allowed_paths:
                    raise ProtocolError(f"Repair escaped original path scope: {value}")
        original_file_paths = {
            str(operation.get("path", "")).strip()
            for operation in previous_operations
            if isinstance(operation, dict) and operation.get("kind") in {"write_text", "replace_text"}
        }
        if not original_file_paths.issubset(repaired_paths):
            raise ProtocolError("Repair omitted an original code file that must be corrected.")
        repaired_signatures = {self._operation_signature(operation.kind, operation.payload) for operation in repaired.operations}
        for operation in previous_operations:
            if not isinstance(operation, dict) or operation.get("kind") in {"write_text", "replace_text", "create_folder"}:
                continue
            payload = {key: value for key, value in operation.items() if key not in {"id", "kind"}}
            signature = self._operation_signature(str(operation.get("kind", "")), payload)
            if signature not in repaired_signatures:
                raise ProtocolError(f"Repair omitted original behavior operation: {signature}")

    @staticmethod
    def _validate_project_grounding(change_set: ChangeSet, context: dict[str, Any], user_prompt: str = "") -> None:
        """Reject invented project APIs, scene targets and asset references before Unity is changed."""
        api = {
            str(item.get("class", "")): set(item.get("public_methods", []))
            for item in context.get("script_api", []) if isinstance(item, dict) and item.get("class")
        }
        fields_by_class = {
            str(item.get("class", "")): set(item.get("public_fields", []))
            for item in context.get("script_api", []) if isinstance(item, dict) and item.get("class")
        }
        scene_targets: set[str] = set()

        def collect_objects(items):
            for item in items if isinstance(items, list) else []:
                if not isinstance(item, dict):
                    continue
                for key in ("name", "path", "hierarchyPath"):
                    value = str(item.get(key, "")).strip()
                    if value:
                        scene_targets.add(value)
                collect_objects(item.get("children", []))

        collect_objects(context.get("scene_objects", []))
        created_targets = {
            str(operation.payload.get("name", "")).strip()
            for operation in change_set.operations
            if operation.kind in {"create_game_object", "create_ui_screen"}
        }
        available_assets = {
            str(path).replace("\\", "/")
            for values in context.get("assets", {}).values()
            for path in (values if isinstance(values, list) else [])
        }
        created_assets = {
            str(operation.payload.get(field, "")).replace("\\", "/")
            for operation in change_set.operations
            for field in ("path", "assetPath", "scenePath")
            if str(operation.payload.get(field, "")).strip()
        }
        all_generated_code = "\n".join(
            str(operation.payload.get("content", operation.payload.get("replacement", "")))
            for operation in change_set.operations if operation.kind in {"write_text", "replace_text"}
        )
        generated_behaviours = set(re.findall(r"\bclass\s+(\w+)\s*:\s*MonoBehaviour\b", all_generated_code))
        attached_components = {
            str(operation.payload.get("component", ""))
            for operation in change_set.operations if operation.kind == "add_component"
        }
        for operation in change_set.operations:
            for component in operation.payload.get("components", []) if isinstance(operation.payload.get("components"), list) else []:
                if isinstance(component, dict):
                    attached_components.add(str(component.get("type", "")))
        normalized_prompt = UnityProjectContext._normalise(user_prompt)
        gameplay_terms = ("bomba", "bomb", "zincir", "chain", "mermi", "projectile", "dusman", "enemy", "patlama", "explosion", "powerup", "combat")
        requires_runtime_wiring = any(word in normalized_prompt for word in gameplay_terms)
        unattached = sorted(name for name in generated_behaviours if name not in attached_components)
        if requires_runtime_wiring and unattached:
            raise ProtocolError(f"Generated gameplay MonoBehaviour scripts are not attached to a scene object or prefab: {unattached}")

        if requires_runtime_wiring and any(word in normalized_prompt for word in ("rastgele", "random")) and "Random." not in all_generated_code:
            raise ProtocolError("The requested random gameplay behavior is missing from generated code.")
        if requires_runtime_wiring and any(word in normalized_prompt for word in ("efekt", "effect", "particle")):
            has_effect_operation = any(operation.kind == "create_effect" for operation in change_set.operations)
            has_existing_effect_reference = any(
                str(operation.payload.get("value", "")).replace("\\", "/") in available_assets
                for operation in change_set.operations if operation.kind == "set_property"
            )
            if not has_effect_operation and not has_existing_effect_reference:
                raise ProtocolError("The requested gameplay effect is neither created nor wired to an existing project asset.")
        incomplete_warning_terms = ("henüz oluşturul", "gerekmektedir", "not created", "must be created", "manual")
        if any(any(term in str(warning).casefold() for term in incomplete_warning_terms) for warning in change_set.warnings):
            raise ProtocolError("The model reported an incomplete dependency in warnings; the change set must include it instead.")
        for operation in change_set.operations:
            if operation.kind in {"add_component", "set_property"}:
                target = str(operation.payload.get("targetPath", "")).strip()
                if scene_targets and target not in scene_targets and target not in created_targets:
                    raise ProtocolError(f"Operation {operation.id} targets an unknown scene GameObject: {target}")
            if operation.kind in {"write_text", "replace_text"}:
                code = str(operation.payload.get("content", operation.payload.get("replacement", "")))
                for class_name, method_name in re.findall(r"\b([A-Z]\w*)\.Instance\.(\w+)\s*\(", code):
                    if class_name in api and method_name not in api[class_name]:
                        raise ProtocolError(f"Generated code calls missing project API {class_name}.Instance.{method_name}(). Available methods: {sorted(api[class_name])}; available public fields: {sorted(fields_by_class.get(class_name, set()))}. Rewrite the adapter using only these members.")
                variable_types = {
                    variable_name: class_name
                    for class_name, variable_name in re.findall(r"\b([A-Z]\w*)\s+(\w+)\s*(?:=|;)", code)
                    if class_name in api
                }
                for variable_name, method_name in re.findall(r"\b(\w+)\.(\w+)\s*\(", code):
                    class_name = variable_types.get(variable_name)
                    if class_name and method_name not in api[class_name]:
                        raise ProtocolError(f"Generated code calls missing project API {class_name}.{method_name}() through '{variable_name}'. Available methods: {sorted(api[class_name])}; available public fields: {sorted(fields_by_class.get(class_name, set()))}. Rewrite the adapter using only these members.")
            if operation.kind == "set_property" and not str(operation.payload.get("component", "")).strip():
                property_name = str(operation.payload.get("property", ""))
                transform_fields = {"position", "localPosition", "rotation", "localRotation", "localScale", "eulerAngles"}
                candidates = [class_name for class_name, fields in fields_by_class.items() if property_name in fields]
                if property_name not in transform_fields:
                    raise ProtocolError(f"Operation {operation.id} set_property must name its component for '{property_name}'. Matching project components: {candidates}")
            property_groups = []
            if isinstance(operation.payload.get("properties"), list):
                property_groups.extend(operation.payload["properties"])
            for component in operation.payload.get("components", []) if isinstance(operation.payload.get("components"), list) else []:
                if isinstance(component, dict) and isinstance(component.get("properties"), list):
                    property_groups.extend(component["properties"])
            if operation.kind == "set_property":
                property_groups.append(operation.payload)
            for prop in property_groups:
                if not isinstance(prop, dict):
                    continue
                asset = str(prop.get("value", "")).replace("\\", "/")
                if asset.startswith("Assets/") and asset not in available_assets and asset not in created_assets:
                    raise ProtocolError(f"Operation {operation.id} references a missing asset: {asset}")

    @staticmethod
    def _operation_signature(kind: str, payload: dict[str, Any]) -> tuple[str, str]:
        target = next((str(payload.get(field, "")) for field in ("name", "targetPath", "assetPath", "scenePath", "path") if payload.get(field)), "")
        return kind, target

    def _visual_context(self, image_path: str, mode: str) -> dict[str, Any]:
        path = Path(image_path)
        if not path.is_file():
            raise FileNotFoundError(f"Reference image not found: {path}")
        return self.vision_router.analyze(path, mode=mode).to_dict()

    def _orchestration_brief(self, prompt: str, context: dict[str, Any], mode: str) -> str:
        """Create a model-to-model handoff before the code specialist emits a change set.

        Qwen 3.6 owns intent decomposition. Qwen Coder receives this bounded brief and
        owns the executable Unity manifest/code. Asset operations remain in the same
        manifest and the executor dispatches them to Flux without another UI action.
        """
        if mode != "local" or not getattr(self.config, "orchestration_enabled", False):
            return ""
        compact_context = {
            "active_scene": context.get("active_scene"),
            "scene_objects": context.get("scene_objects", []),
            "script_api": context.get("script_api", []),
            "available_assets": context.get("assets", {}),
            "unity_documentation": context.get("unity_documentation", []),
        }
        return self.router.generate(
            "Decompose this one Unity request into a specialist handoff JSON. JSON only. "
            "behavior: requested Unity outcome; distribution: implementation responsibilities and which outputs need code, image assets or 3D assets; "
            "feedback: visual/audio requirements; integration: exact project targets; acceptance: observable checks. "
            "Do not write final code or a change-set. Use only supplied project APIs/assets.\n"
            + prompt + "\nProject evidence:\n" + json.dumps(compact_context, ensure_ascii=False),
            task="feature_analysis",
            system="You are the orchestration planner. Return behavior, distribution, feedback, integration and acceptance arrays. State which specialist should produce each artifact: qwen3-coder for C# or Unity wiring, Flux.2 for 2D images, and Hunyuan 3D only when its provider is installed. Explicitly cover how features are triggered and integrated.",
            mode=mode,
        )

    def _planning_prompt(self, prompt: str, context: dict[str, Any], visual: dict[str, Any] | None, feature_blueprint: str = "") -> str:
        visual_text = json.dumps(visual, ensure_ascii=False, indent=2) if visual else "No reference image supplied."
        requested_language = str(context.get("requested_language", "Turkish"))
        return f"""Create an executable, reviewable Unity change set for this request:
{prompt}

Unity project context (bounded, real project data):
{self.context_builder.as_prompt(context)}

Reference-image analysis:
{visual_text}

Mandatory specialist handoff from the first local reasoning pass:
{feature_blueprint or "Not required for this request."}

Attached reference image asset path: {str(context.get("reference_image_path", ""))}

Produce every operation required for a complete result. You are the code/Unity specialist: include code, scene/prefab/effect operations and validation as appropriate. When the handoff calls for a 2D asset, include generate_image in this same change set; Unity will dispatch it to Flux.2 automatically. If an attached reference image must be modified, set generate_image.sourceImagePath to the attached reference asset path and use an explicit edit prompt. When the handoff calls for a 3D asset and no installed provider is listed in project context, return a bounded build_character placeholder plan or an answer explaining the missing provider; never pretend a Hunyuan mesh was generated. Implement every applicable handoff responsibility and acceptance item; do not move missing work into warnings.

MANDATORY OUTPUT LANGUAGE: {requested_language}. All user-visible JSON fields (summary, answer, explanation, warnings and validation.checks) must be {requested_language}; do not use the other language."""
