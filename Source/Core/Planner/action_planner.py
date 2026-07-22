from Source.Core.Models.action_plan import ActionPlan
from Source.Core.Knowledge.script_knowledge import ScriptKnowledge

class ActionPlanner:

    def __init__(self):

        self.knowledge = ScriptKnowledge()
        from Source.Core.Critique.plan_critic import PlanCritic
        from Source.Core.Critique.critique_ledger import CritiqueLedger
        from Source.Core.Config.config_manager import ConfigManager
        from Source.Knowledge.unity_expertise import UnityExpertise
        from Source.Memory.learning_memory import LearningMemory
        self.critic = PlanCritic()
        self.critique_ledger = CritiqueLedger()
        self.unity_expertise = UnityExpertise(ConfigManager().project_root)
        self.learning_memory = LearningMemory()

    def build(self, command):
        return self._finalize(self._build(command), command)

    def _build(self, command):

        plan = ActionPlan()

        end_to_end = command.metadata.get("end_to_end_game_plan")
        game_plan = command.metadata.get("game_scaffold_plan")
        if end_to_end and game_plan:
            plan.action = "BUILD_GAME_FROM_REFERENCE"
            plan.target = game_plan["game_name"]
            plan.confidence = 0.85
            plan.risk = "HIGH"
            plan.steps = [
                "phase5_visual_analysis",
                "phase7_scene_and_mechanics_generation",
                "phase2_compile_playmode_validation_and_repair",
            ]
            plan.context = {
                "reference_image": end_to_end["reference_image"],
                "visual_summary": end_to_end["visual_summary"],
                "phase_chain": end_to_end["phase_chain"],
                "game_key": end_to_end["game_key"],
                "scene_path": end_to_end["scene_path"],
                "acceptance_signals": end_to_end["acceptance_signals"],
                "build_request": command.metadata["game_build_request"],
                "requires_review": True,
            }
            return plan

        if game_plan:
            plan.action = "BUILD_GAME_PROTOTYPE"
            plan.target = game_plan["game_name"]
            plan.confidence = 0.85
            plan.risk = "HIGH"
            plan.steps = list(game_plan["progress_stages"])
            plan.context = {
                "game_key": game_plan["game_key"],
                "scene_path": game_plan["scene_path"],
                "systems": game_plan["systems"],
                "acceptance_signals": game_plan["acceptance_signals"],
                "build_request": command.metadata["game_build_request"],
                "requires_review": True,
            }
            return plan

        character_plan = command.metadata.get("character_prefab_plan")
        if character_plan:
            plan.action = "BUILD_CHARACTER_PREFAB"
            plan.target = command.target
            plan.confidence = character_plan["profile"]["confidence"]
            plan.risk = "MEDIUM"
            plan.steps = character_plan["operations"]
            plan.context = {
                "character_profile": character_plan["profile"],
                "physics": character_plan["physics"],
                "animator": character_plan["animator"],
                "prefab_path": character_plan["prefab_path"],
                "warnings": character_plan["warnings"],
                "requires_review": character_plan["requires_review"],
            }
            return plan

        visual_plan = command.metadata.get("visual_build_plan")
        if visual_plan:
            plan.action = "BUILD_FROM_IMAGE"
            plan.target = command.target or "VisualReference"
            plan.confidence = 0.80
            plan.risk = "MEDIUM"
            plan.steps = visual_plan.get("commands", [])
            plan.context = {
                "image_path": command.parameters.get("image_path"),
                "visual_analysis": command.metadata.get("visual_analysis", {}),
                "warnings": visual_plan.get("warnings", []),
                "summary": visual_plan.get("summary", ""),
                "unity_context": visual_plan.get("unity_context", {}),
            }
            return plan

        plan.action = command.intent

        plan.target = command.target

        if command.target == "Ball":

            plan.target_class = "BallChainManager"

        elif command.target == "Wolf":

            plan.target_class = "HealthManager"

        if command.parameters.get("color"):

            plan.value = command.parameters["color"]

        speed = self.knowledge.find_field("speed")

        if speed:

            plan.target_field = "speed"

            plan.context["speed_locations"] = speed

        plan.confidence = 0.90

        plan.risk = "HIGH" if command.intent in {"DELETE_OBJECT", "DELETE_FILE", "REFACTOR"} else "LOW"

        plan.steps = [
            "Locate target class",
            "Locate target field",
            "Generate modification",
            "Validate"
        ]

        return plan

    def _finalize(self, plan, command):
        lessons = self.learning_memory.relevant_for(command.prompt)
        plan.warnings = [warning.to_dict() for warning in self.critic.critique(command, plan, self.unity_expertise)]
        for lesson in lessons:
            plan.warnings.append({
                "code": f"learned_{lesson.code}",
                "severity": lesson.severity,
                "issue": "A similar risk was recorded in a previous task.",
                "rationale": lesson.lesson,
                "alternative": lesson.alternative,
                "requires_consent": lesson.severity == "HIGH",
                "occurrences": lesson.occurrences,
            })
        plan.context["learned_lessons"] = [lesson.to_dict() for lesson in lessons]
        plan.context["requires_informed_consent"] = any(warning["requires_consent"] for warning in plan.warnings)
        plan.context["execution_authorized"] = not plan.context["requires_informed_consent"]
        new_warnings = [warning for warning in plan.warnings if not warning["code"].startswith("learned_")]
        event = self.critique_ledger.record(command, new_warnings)
        if event:
            plan.context["phase10_memory_handoff"] = event
        return plan

    @staticmethod
    def apply_user_reply(plan, reply):
        from Source.Core.Critique.consent import ConsentParser
        return ConsentParser().apply_reply(plan, reply)
