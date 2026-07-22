from Source.Knowledge.retriever import Retriever
from Source.Knowledge.Reflection.reflection_retriever import ReflectionEngine
from Source.Knowledge.document_knowledge import DocumentKnowledge
from Source.Knowledge.unity_expertise import UnityExpertise
from Source.Core.Config.config_manager import ConfigManager
from Source.Brain.prompt_builder import PromptBuilder
from Source.LLM.client import LLMClient
from Source.LLM.prompt import SYSTEM_PROMPT
from Source.LLM.workflow_parser import WorkflowParser
from Source.Planner.planner import Planner
from Source.Core.Pipeline.command_pipeline import CommandPipeline
from Source.Core.Fusion.visual_fusion import VisualFusionEngine
from Source.Core.Planner.action_planner import ActionPlanner
from Source.Core.Character.character_pipeline import CharacterGenerationPipeline

import traceback


class Brain:

    def __init__(self):

        self.retriever = Retriever()

        self.reflection = ReflectionEngine()
        self.command_pipeline = CommandPipeline()
        self.visual_fusion = VisualFusionEngine()
        self.visual_planner = ActionPlanner()
        self.character_pipeline = CharacterGenerationPipeline()
        self.documents = DocumentKnowledge()
        self.unity_expertise = UnityExpertise(ConfigManager().project_root)

        self.builder = PromptBuilder()

        self.client = LLMClient()

        self.parser = WorkflowParser()

        self.planner = Planner()


    def think(self, request):

        try:

            print("=" * 60)
            print("BRAIN")
            print("=" * 60)

            context = {

                                "scene":
                    self.retriever.scene_objects(),

                "reflection": {

                    "classes":
                        self.reflection.count(),

                    "assemblies":
                        self.reflection.assemblies()

                },

                "project":{

                    "prefabs":[
                        x["name"]
                        for x in self.retriever.project_assets_by_type(
                            "Prefab"
                        )
                    ],

                    "materials":[
                        x["name"]
                        for x in self.retriever.project_assets_by_type(
                            "Material"
                        )
                    ],

                    "textures":[
                        x["name"]
                        for x in self.retriever.project_assets_by_type(
                            "Texture"
                        )
                    ],

                    "audio":[
                        x["name"]
                        for x in self.retriever.project_assets_by_type(
                            "Audio"
                        )
                    ],

                    "scripts":[
                        x["name"]
                        for x in self.retriever.project_assets_by_type(
                            "Script"
                        )
                    ],

                    "animations":[
                        x["name"]
                        for x in self.retriever.project_assets_by_type(
                            "Animation"
                        )
                    ]

                }

            }

            print("Scene Objects :", len(context["scene"]))
            print("Prefabs      :", len(context["project"]["prefabs"]))
            print("Materials    :", len(context["project"]["materials"]))
            print("Textures     :", len(context["project"]["textures"]))
            print("Reflection   :", context["reflection"]["classes"])

            command = self.command_pipeline.process(request)

            context["command"] = command.to_dict()

            context["documents"] = self.documents.get_document(request)
            context["unity_expertise"] = self.unity_expertise.context_for(
                request,
                context["documents"],
            )

            print("Intent       :", command.intent)
            print("Target       :", command.target)
            print("Docs found   :", len(context["documents"]))
            prompt = (

                SYSTEM_PROMPT

                + "\n\n"

                + self.builder.build(

                    request,

                    context

                )

            )

            prompt = prompt.replace(
                "\ufeff",
                ""
            )

            print("Prompt Ready")

            print(">>> BEFORE LLM")

            response = self.client.generate(
                prompt
            )

            print(">>> AFTER LLM")

            print("=" * 60)
            print("LLM RESPONSE")
            print("=" * 60)
            print(response)
            print("=" * 60)

            print("LLM Finished")

            print(">>> BEFORE PARSER")

            tasks = self.parser.parse(
                response
            )

            print(">>> AFTER PARSER")

            print("Parser Finished")

            print(">>> BEFORE PLANNER")

            tasks = self.planner.plan(
                tasks
            )

            print(">>> AFTER PLANNER")

            print("Planner Finished")

            return tasks

        except Exception:

            print()

            print("=" * 60)
            print("BRAIN ERROR")
            print("=" * 60)

            traceback.print_exc()

            raise

    def analyze_image(self, image_path, request="Bu referans görseldeki Unity ekranını kur"):
        """Return a reviewable Unity action plan sourced from an image reference."""
        command = self.command_pipeline.process_image(request, image_path, self.visual_fusion.vision_client)
        return self.visual_planner.build(command)

    def generate_character_from_image(self, image_path, request="Bu karakter görselinden prefab oluştur", name=None):
        command = self.command_pipeline.process_character_image(request, image_path, self.character_pipeline.vision_client, name)
        return self.visual_planner.build(command)




