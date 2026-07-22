class PromptBuilder:

    def build(self, question, context):

        lines = []

        lines.append(
            "You are AI Engineer."
        )

        lines.append("")

        lines.append(
            "UNITY SCENE"
        )

        lines.append(
            "================================================"
        )

        for obj in context.get("scene", []):

            lines.append(
                f"Object : {obj.get('name','')}"
            )

            if obj.get("path"):
                lines.append(
                    f"Path : {obj.get('path')}"
                )

            if obj.get("parent"):
                lines.append(
                    f"Parent : {obj.get('parent')}"
                )

            children = obj.get(
                "children",
                []
            )

            if isinstance(children, str):
                children = []

            if children:

                lines.append("Children :")

                for child in children:
                    lines.append(
                        f"  - {child}"
                    )

            comps = obj.get(
                "components",
                []
            )

            if isinstance(comps, str):
                comps = []

            if comps:

                lines.append("Components :")

                for c in comps:
                    lines.append(
                        f"  - {c}"
                    )

            lines.append("")

        project = context.get(
            "project",
            {}
        )

        lines.append("")
        lines.append(
            "AVAILABLE PREFABS"
        )
        lines.append(
            "================================================"
        )

        for p in project.get(
            "prefabs",
            []
        ):
            lines.append(
                p
            )

        lines.append("")
        lines.append(
            "AVAILABLE MATERIALS"
        )
        lines.append(
            "================================================"
        )

        for m in project.get(
            "materials",
            []
        ):
            lines.append(
                m
            )

        documents = context.get(
            "documents",
            []
        )

        if documents:

            lines.append("")
            lines.append(
                "UNITY DOCUMENTATION"
            )
            lines.append(
                "================================================"
            )

            for doc in documents:

                lines.append(
                    f"Title : {doc.get('title', '')}"
                )

                lines.append(
                    f"Section : {doc.get('section', '')}"
                )

                for p in doc.get("paragraphs", []):
                    lines.append(
                        f"  {p}"
                    )

                for code in doc.get("code_blocks", []):
                    lines.append(
                        "  Code:"
                    )
                    lines.append(
                        f"  {code}"
                    )

                lines.append("")

        lines.append("")
        unity_expertise = context.get("unity_expertise", {})

        if unity_expertise:

            lines.append("")
            lines.append("UNITY EXPERTISE")
            lines.append("================================================")
            lines.append(f"Render Pipeline : {unity_expertise.get('render_pipeline', 'Unknown')}")

            for item in unity_expertise.get("expertise", []):
                lines.append(f"Topic : {item.get('topic', '')}")
                for rule in item.get("rules", []):
                    lines.append(f"  - {rule}")
                for pitfall in item.get("pitfalls", []):
                    lines.append(f"  - Pitfall: {pitfall}")

            recommendation = unity_expertise.get("recommendation", {})
            if recommendation:
                lines.append(f"Allowed : {recommendation.get('allowed', True)}")
                lines.append(f"Recommendation : {recommendation.get('reason', '')}")
                if recommendation.get("alternative"):
                    lines.append(f"Alternative : {recommendation['alternative']}")

            for document in unity_expertise.get("documentation", []):
                lines.append(
                    f"Documentation : {document.get('title', '')} / {document.get('section', '')}"
                )

        visual = context.get("visual_analysis", {})
        if visual:
            lines.append("")
            lines.append("VISUAL ANALYSIS")
            lines.append("================================================")
            lines.append(f"Camera : {visual.get('camera', {}).get('angle', 'unknown')} / {visual.get('camera', {}).get('projection', 'unknown')}")
            lines.append(f"Assets : {visual.get('assets', {}).get('dimension', 'unknown')} / {visual.get('assets', {}).get('style', '')}")
            for element in visual.get("ui", []):
                lines.append(f"UI : {element.get('kind', '')} / {element.get('label', '')}")

        lines.append(
            "USER REQUEST"
        )

        lines.append(
            "================================================"
        )

        lines.append(
            question
        )

        lines.append("")
        lines.append(
            "IMPORTANT RULES"
        )

        lines.append(
            "- Use ONLY Unity objects from the scene."
        )

        lines.append(
            "- Use ONLY prefabs from AVAILABLE PREFABS."
        )

        lines.append(
            "- Never invent prefab names."
        )

        lines.append(
            "- If the requested prefab does not exist, NEVER use FindPrefab."
        )

        lines.append(
            "- If the requested effect does not exist, create it using Unity instead."
        )

        lines.append(
            "- Think before generating JSON."
        )

        lines.append(
            "- Return ONLY valid JSON."
        )

        return "\n".join(lines)

