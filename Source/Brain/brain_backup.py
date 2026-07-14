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

        tasks = self.planner.plan(request)

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

        first = result["tasks"][0]

        return Action(

            action=first.action,

            target=first.target,

            effect="Magic fire pro blue"

        )
