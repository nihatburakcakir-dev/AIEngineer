from Source.Brain.intent_parser import IntentParser
from Source.Brain.router import Router
from Source.Brain.executor import Executor
from Source.Brain.result import BrainResult

from Source.Brain.Handlers.modify_variable import ModifyVariableHandler


class Orchestrator:

    def __init__(

        self,

        registry

    ):

        self.parser = IntentParser()

        self.router = Router()

        self.router.register(

            ModifyVariableHandler()

        )

        self.executor = Executor(

            registry

        )

    def execute(

        self,

        command

    ):

        intent = self.parser.parse(

            command

        )

        handler = self.router.resolve(

            intent

        )

        if handler is None:

            print(

                "No handler."

            )

            return BrainResult(

                success=False,

                message="No handler.",

                data={"intent": intent.name}

            )

        plan = handler.execute(

            intent

        )

        success = self.executor.execute(

            plan

        )

        return BrainResult(

            success=success,

            message="OK" if success else "Execution stopped.",

            data={"intent": intent.name}

        )
