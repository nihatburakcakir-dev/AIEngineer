class PromptBuilder:

    def build(self, question, context):

        lines = []

        lines.append(
            "You are an expert Unity and C# engineer."
        )

        lines.append("")

        lines.append("PROJECT CONTEXT")

        lines.append("----------------")

        for item in context:

            lines.append(
                f"FILE : {item.get('path','')}"
            )

            analysis = item.get(
                "analysis",
                {}
            )

            cls = analysis.get("class")

            if cls:

                lines.append(
                    f"CLASS : {cls}"
                )

            methods = analysis.get(
                "methods",
                []
            )

            if methods:

                lines.append(
                    "METHODS :"
                )

                for m in methods:

                    lines.append(
                        f" - {m}"
                    )

            fields = analysis.get(
                "fields",
                []
            )

            if fields:

                lines.append(
                    "FIELDS :"
                )

                for f in fields:

                    lines.append(
                        f" - {f}"
                    )

            lines.append("")

        lines.append("----------------")

        lines.append("QUESTION")

        lines.append(question)

        return "\n".join(lines)
