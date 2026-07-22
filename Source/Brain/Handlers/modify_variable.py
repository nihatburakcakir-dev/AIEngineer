from Source.Brain.Models.plan import Plan
from Source.Brain.Models.step import Step


class ModifyVariableHandler:

    def can_handle(self, intent):

        return intent.name == "modify_variable"

    def execute(self, intent):

        plan = Plan()

        plan.add_step(

            Step(

                tool="ScriptSearch",

                action="find",

                parameters={

                    "script": intent.target

                }

            )

        )

        plan.add_step(

            Step(

                tool="Backup",

                action="create",

                parameters={

                    "script": intent.target

                }

            )

        )

        plan.add_step(

            Step(

                tool="Patch",

                action="modify_variable",

                parameters=intent.parameters

            )

        )

        plan.add_step(

            Step(

                tool="Compile",

                action="compile"

            )

        )

        plan.add_step(

            Step(

                tool="Validate",

                action="validate"

            )

        )

        return plan
