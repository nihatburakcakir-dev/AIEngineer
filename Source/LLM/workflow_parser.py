import json

from Source.Planner.models import Task


class WorkflowParser:

    def parse(self, text: str):

        data = json.loads(text)

        tasks = []

        for item in data["tasks"]:

            tasks.append(

                Task(

                    item["action"],

                    item.get("target", "")

                )

            )

        return tasks
