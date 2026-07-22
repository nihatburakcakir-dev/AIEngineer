"""Bridge image analysis into command and planner metadata."""

from Source.Core.Vision.unity_visual_mapper import UnityVisualMapper
from Source.Core.Vision.vision_client import VisionClient
from Source.Core.Config.config_manager import ConfigManager
from Source.Knowledge.unity_expertise import UnityExpertise


class VisualFusionEngine:
    def __init__(self, vision_client=None, mapper=None):
        config = ConfigManager()
        self.vision_client = vision_client or VisionClient(config.vision_model, config.vision_endpoint)
        self.mapper = mapper or UnityVisualMapper(UnityExpertise(config.project_root))

    def analyze_and_plan(self, image_path):
        analysis = self.vision_client.analyze(image_path)
        plan = self.mapper.map(analysis)
        return analysis, plan

    def attach(self, command, image_path):
        analysis, plan = self.analyze_and_plan(image_path)
        command.intent = "BUILD_FROM_IMAGE"
        command.target = "VisualReference"
        command.parameters["image_path"] = str(image_path)
        command.metadata["visual_analysis"] = analysis.to_dict()
        command.metadata["visual_build_plan"] = plan.to_dict()
        return command
