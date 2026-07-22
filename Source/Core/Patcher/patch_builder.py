from Source.Core.Models.code_patch import CodePatch
from Source.Core.Knowledge.script_knowledge import ScriptKnowledge

class PatchBuilder:

    def __init__(self):

        self.knowledge = ScriptKnowledge()

    def build(self, plan):

        patch = CodePatch()

        patch.action = plan.action
        patch.operation = plan.operation
        patch.value = plan.value

        cls = self.knowledge.find_class(
            plan.target_class
        )

        if cls:

            patch.file = cls["path"]

        patch.target = plan.target_field

        patch.description = (
            f"{plan.operation} "
            f"{plan.target_field} "
            f"{plan.value}"
        )

        patch.metadata = {
            "class": plan.target_class,
            "field": plan.target_field
        }

        return patch
