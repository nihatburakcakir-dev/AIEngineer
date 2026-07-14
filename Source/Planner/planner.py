from Source.Planner.models import Task


class Planner:

    def plan(self, tasks):

        print("=" * 60)
        print("PLANNER")
        print("=" * 60)

        if tasks is None:

            raise Exception(
                "Workflow is null."
            )

        if len(tasks) == 0:

            raise Exception(
                "Workflow contains no task."
            )

        print(
            "Task Count :",
            len(tasks)
        )

        return tasks
