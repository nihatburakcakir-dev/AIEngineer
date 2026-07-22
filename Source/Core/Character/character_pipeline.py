from Source.Core.Character.character_generator import CharacterClassifier, CharacterPrefabGenerator
from Source.Core.Vision.vision_client import VisionClient


class CharacterGenerationPipeline:
    def __init__(self, vision_client=None, classifier=None, generator=None):
        self.vision_client = vision_client or VisionClient()
        self.classifier = classifier or CharacterClassifier()
        self.generator = generator or CharacterPrefabGenerator()

    def plan_from_image(self, image_path, name=None):
        analysis = self.vision_client.analyze(image_path)
        profile = self.classifier.classify(analysis, image_path, name)
        return self.generator.build_plan(profile)

    def attach(self, command, image_path, name=None):
        plan = self.plan_from_image(image_path, name)
        command.intent = "BUILD_CHARACTER_PREFAB"
        command.target = plan.profile.name
        command.parameters["image_path"] = str(image_path)
        command.metadata["character_prefab_plan"] = plan.to_dict()
        return command
