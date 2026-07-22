"""Select local or explicitly requested cloud vision without weakening strict parsing."""

from pathlib import Path

from Source.Core.Vision.image_parser import ImageParser
from Source.Core.Vision.vision_client import VisionClient
from Source.LLM.cloud_client import OpenRouterClient


class OptionalVisionRouter:
    def __init__(self, config, cloud_factory=None, local_factory=None):
        self.config = config
        self.cloud_factory = cloud_factory or OpenRouterClient
        self.local_factory = local_factory or VisionClient

    def analyze(self, image_path, mode="local"):
        if mode in {"local", "qwen_code", "codex"}:
            return self.local_factory(self.config.vision_model, self.config.vision_endpoint).analyze(image_path)
        if mode != "cloud":
            raise ValueError("Vision mode must be 'local', 'qwen_code', 'codex' or 'cloud'.")
        client = self.cloud_factory(self.config.cloud_model_for("vision"), self.config.cloud_api_key, self.config.cloud_endpoint)
        content = client.analyze_image(image_path, VisionClient.STRUCTURED_PROMPT)
        return ImageParser().parse(Path(image_path), content, model=client.model)
