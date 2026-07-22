class CodeGenerator:

    def generate(self, plan):

        if plan.action == "MODIFY_FIELD":

            return {
                "type":"field_update",
                "class":plan.target_class,
                "field":plan.target_field,
                "operation":plan.operation,
                "value":plan.value
            }

        if plan.action == "CHANGE_COLOR":

            return {
                "type":"color_change",
                "class":plan.target_class,
                "color":plan.value
            }

        return {
            "type":"unknown"
        }

    def generate_for_request(self, request, expertise):
        """Generate a vetted template constrained by the active Unity pipeline."""
        recommendation = expertise.recommend(request)
        if not recommendation.get("allowed", True):
            return {
                "type": "blocked",
                "pipeline": expertise.render_pipeline(),
                "reason": recommendation.get("reason", "Request is incompatible with the active project."),
                "alternative": recommendation.get("alternative"),
            }
        template = expertise.code_template(request)
        if template is None:
            return {"type": "unknown", "pipeline": expertise.render_pipeline()}
        return {"type": "unity_template", **template}
