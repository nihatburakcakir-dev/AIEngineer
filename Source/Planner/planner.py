import unicodedata

from Source.Planner.models import Task


class Planner:

    def normalize(self, text: str):

        text = text.lower()

        return (
            unicodedata.normalize(
                "NFKD",
                text
            )
            .encode(
                "ascii",
                "ignore"
            )
            .decode("ascii")
        )


    def plan(self, request: str):

        text = self.normalize(request)

        print("=" * 60)
        print("PLANNER INPUT")
        print(text)
        print("=" * 60)

        tasks = []

        if (
            "ates" in text
            or "fire" in text
        ):

            tasks.append(
                Task(
                    "FindObject",
                    "WolfMouth"
                )
            )

            tasks.append(
                Task(
                    "FindPrefab",
                    "Magic fire pro blue"
                )
            )

            tasks.append(
                Task(
                    "Instantiate"
                )
            )

            tasks.append(
                Task(
                    "SetParent",
                    "WolfMouth"
                )
            )

            tasks.append(
                Task(
                    "ResetTransform"
                )
            )

        print("TASKS :", len(tasks))

        return tasks
