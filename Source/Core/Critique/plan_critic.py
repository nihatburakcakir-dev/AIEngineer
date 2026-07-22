"""Pre-execution engineering critique with explicit, reversible user consent."""

from dataclasses import asdict, dataclass
import re


@dataclass(frozen=True)
class EngineeringWarning:
    code: str
    severity: str
    issue: str
    rationale: str
    alternative: str
    requires_consent: bool = True

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class UserDecision:
    approved: bool
    reason: str = ""


class PlanCritic:
    """Small deterministic rule set; it warns before a risky plan reaches execution."""

    def critique(self, command, plan, expertise=None):
        source = " ".join([command.prompt or "", str(plan.steps)]).casefold()
        warnings = []
        if self._contains_update_allocation(source):
            warnings.append(EngineeringWarning(
                "per_frame_allocation", "HIGH",
                "Plan proposes allocating or instantiating objects every frame.",
                "Per-frame allocations and Instantiate/Destroy calls create garbage collection pressure and frame spikes in Unity.",
                "Use an object pool and trigger creation from gameplay events instead of Update.",
            ))
        if self._contains_update_lookup(source):
            warnings.append(EngineeringWarning(
                "per_frame_component_lookup", "MEDIUM",
                "Plan proposes GetComponent work every frame.",
                "Repeated component lookup in Update wastes CPU time, especially across many objects.",
                "Cache the component reference in Awake or Start.",
            ))
        if re.search(r"(rigidbody|addforce).{0,120}update|update.{0,120}(rigidbody|addforce)", source):
            warnings.append(EngineeringWarning(
                "physics_in_update", "MEDIUM",
                "Plan applies Rigidbody physics work from Update.",
                "Update runs at a variable rate, so force application becomes frame-rate dependent.",
                "Move Rigidbody force and velocity work to FixedUpdate.",
            ))
        if re.search(r"renderer\.material.{0,120}(update|frame)|(update|frame).{0,120}renderer\.material", source):
            warnings.append(EngineeringWarning(
                "per_frame_material_instance", "MEDIUM",
                "Plan accesses Renderer.material in a per-frame path.",
                "Renderer.material can create material instances and increase memory use.",
                "Cache a MaterialPropertyBlock or use shared assets when per-instance values are not needed.",
            ))
        if plan.risk == "HIGH" and plan.action in {"DELETE_OBJECT", "DELETE_FILE", "REFACTOR"}:
            warnings.append(EngineeringWarning(
                "high_impact_change", "HIGH",
                "Plan changes or removes existing project content.",
                "A broad refactor or deletion can break references outside the selected target.",
                "Create a scoped patch, run validation, and keep rollback material before applying it.",
            ))
        warnings.extend(self._expertise_warnings(command, expertise))
        warnings.extend(self._phase4_tool_warnings(command))
        return self._unique(warnings)

    @staticmethod
    def apply_decision(plan, decision: UserDecision):
        plan.context["user_decision"] = asdict(decision)
        plan.context["execution_authorized"] = bool(decision.approved) or not bool(plan.warnings)
        return plan

    @staticmethod
    def _contains_update_allocation(source):
        return bool(re.search(r"(her|every)\s*(frame|update).{0,100}(instantiate|destroy|new\s+gameobject|allocation)|update.{0,160}(instantiate|destroy|new\s+gameobject)", source))

    @staticmethod
    def _contains_update_lookup(source):
        return bool(re.search(r"(her|every)\s*(frame|update).{0,100}getcomponent|update.{0,160}getcomponent", source))

    @staticmethod
    def _unique(warnings):
        result, seen = [], set()
        for warning in warnings:
            if warning.code not in seen:
                result.append(warning)
                seen.add(warning.code)
        return result

    @staticmethod
    def _expertise_warnings(command, expertise):
        if expertise is None:
            return []
        recommendation = expertise.recommend(command.prompt or "")
        if recommendation.get("allowed", True):
            return []
        return [EngineeringWarning(
            "unity_expertise_constraint", "HIGH",
            "Plan conflicts with the current Unity project configuration.",
            recommendation.get("reason", "Unity expertise rejected the request."),
            recommendation.get("alternative", "Use APIs compatible with the active Unity project."),
        )]

    @staticmethod
    def _phase4_tool_warnings(command):
        from pathlib import Path
        from Source.Core.Tools.Builtin.performance_tool import PerformanceTool

        warnings = []
        for candidate in list(command.scripts) + list(command.assets):
            path = Path(candidate)
            if not path.is_file() or path.suffix.casefold() != ".cs":
                continue
            for finding in PerformanceTool().analyze(path):
                warnings.append(EngineeringWarning(
                    f"faz4_performance_{finding['rule']}", finding["severity"],
                    f"Faz 4 performance analysis found {finding['rule']} in {path.name}.",
                    "The existing static analysis identified a Unity performance anti-pattern in the selected file.",
                    finding["recommendation"],
                ))
        return warnings
