from Source.Knowledge.retriever import Retriever
from Source.Brain.prompt_builder import PromptBuilder

from Source.LLM.client import LLMClient
from Source.LLM.prompt import SYSTEM_PROMPT
from Source.LLM.workflow_parser import WorkflowParser

from Source.Planner.planner import Planner


class Brain:

    def __init__(self):

        self.retriever = Retriever()

        self.builder = PromptBuilder()

        self.client = LLMClient()

        self.parser = WorkflowParser()

        self.planner = Planner()


    def think(self, request):

        print("=" * 60)
        print("BRAIN")
        print("=" * 60)

        context = {

            "scene":
                self.retriever.scene_objects(),

            "files":[]
        }

        prompt = (

            SYSTEM_PROMPT

            + "\n\n"

            + self.builder.build(

                request,

                context

            )

        )

        print()
        print(prompt)

        response = self.client.generate(
            prompt
        )

        print()
        print("LLM RESPONSE")
        print("=" * 60)
        print(response)

        tasks = self.parser.parse(
            response
        )

        tasks = self.planner.plan(
            tasks
        )

        return tasks
