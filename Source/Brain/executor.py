class Executor:

    def __init__(

        self,

        registry

    ):

        self.registry = registry

    def execute(

        self,

        plan

    ):

        print()

        print("Executing Plan")

        print("----------------")

        for step in plan:

            tool = self.registry.get(

                step.tool

            )

            if tool is None:

                raise Exception(

                    f"Tool not found : {step.tool}"

                )

            ok = tool.execute(step)

            if not ok:

                print()

                print(

                    "Execution stopped."

                )

                return False

        return True
