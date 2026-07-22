from pathlib import Path


class ExampleLoader:

    def load(self):

        root = (
            Path(__file__).parent
            / "Examples"
        )

        sections = []

        for file in sorted(
            root.rglob("*.txt")
        ):

            text = file.read_text(
                encoding="utf-8-sig"
            )

            text = text.replace(
                "\ufeff",
                ""
            )

            sections.append(
                text
            )

        return "\n\n".join(
            sections
        )
