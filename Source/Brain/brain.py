from dataclasses import dataclass

from Source.Planner.planner import Planner
from Source.Knowledge.retriever import Retriever
from Source.Brain.prompt_builder import PromptBuilder


@dataclass
class Action:

    action: str
    target: str
    effect: str = ""


class Brain:

    def __init__(self):

        self.planner = Planner()

        self.retriever = Retriever()

        self.builder = PromptBuilder()


    def think(self, request):

        print("=" * 60)
        print("BRAIN REQUEST")
        print(request)
        print("=" * 60)

        tasks = self.planner.plan(request)

        print("TASK COUNT :", len(tasks))

        for t in tasks:
            print(t)

        context = []

        for task in tasks:

            if task.target:

                context.extend(
                    self.retriever.search_name(
                        task.target
                    )
                )

        prompt = self.builder.build(
            request,
            context
        )

        return {

            "tasks": tasks,

            "context": context,

            "prompt": prompt

        }


    def understand(self, text, context):

        result = self.think(text)

        if len(result["tasks"]) == 0:

            raise Exception(
                "Planner produced no task."
            )

        first = result["tasks"][0]

        return Action(

            action=first.action,

            target=first.target,

            effect="Magic fire pro blue"

        )
