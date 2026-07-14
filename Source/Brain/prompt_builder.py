class PromptBuilder:

    def build(self, question, context):

        lines = []

        lines.append(
            "You are an expert Unity Engineer."
        )

        lines.append("")

        lines.append(
            "UNITY SCENE OBJECTS"
        )

        lines.append(
            "------------------------"
        )

        for obj in context.get("scene", []):

            lines.append(

                obj.get(
                    "name",
                    ""
                )

            )

        lines.append("")

        lines.append(
            "USER REQUEST"
        )

        lines.append(
            "------------------------"
        )

        lines.append(
            question
        )

        lines.append("")

        lines.append(
            "Rules"
        )

        lines.append(
            "- Use ONLY Unity object names above."
        )

        lines.append(
            "- Never invent object names."
        )

        lines.append(
            "- Return JSON only."
        )

        return "\n".join(lines)
