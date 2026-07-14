from Core.task import Task


class Planner:

    def create_plan(self, command: str):

        task = Task(
            id="001",
            command=command
        )

        return task
