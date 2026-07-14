from Source.Planner.models import Task


class Planner:

    def plan(self, request: str):

        text = request.lower()

        tasks = []

        if "ateş" in text or "fire" in text:

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

        return tasks
