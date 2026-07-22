import os

from Source.Core.Knowledge.script_knowledge import ScriptKnowledge
from Source.Core.Executor.file_executor import FileExecutor

class PatchValidator:

    def __init__(self):

        self.knowledge = ScriptKnowledge()
        self.files = FileExecutor()

    def validate(self, patch):

        result = {
            "valid": True,
            "risk": "LOW",
            "warnings": [],
            "errors": []
        }

        if not patch.file:

            result["valid"] = False
            result["errors"].append("Patch file is empty.")
            return result

        if not self.files.exists(patch.file):

            result["valid"] = False
            result["errors"].append("Target file not found.")

        metadata = patch.metadata or {}
        class_name = metadata.get("class", "")
        field_name = metadata.get("field", "")

        if not class_name or not field_name:

            result["valid"] = False
            result["errors"].append("Patch metadata must include class and field.")
            return result

        cls = self.knowledge.find_class(class_name)

        if cls is None:

            result["valid"] = False
            result["errors"].append("Target class not found.")

        field = self.knowledge.find_field(field_name)

        if len(field) == 0:

            result["valid"] = False
            result["errors"].append("Target field not found.")

        if patch.action not in {

            "MODIFY_FIELD",
            "CHANGE_COLOR",
            "CREATE_OBJECT",
            "DELETE_OBJECT"
        }:

            result["warnings"].append(
                "Unknown patch action."
            )

        if patch.operation == "":

            result["warnings"].append(
                "Operation is empty."
            )

        if patch.value is None:

            result["warnings"].append(
                "Patch value is empty."
            )

        if len(result["errors"]) > 0:

            result["risk"] = "HIGH"

        elif len(result["warnings"]) > 0:

            result["risk"] = "MEDIUM"

        return result
