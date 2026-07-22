from Source.Core.Parser.command_parser import CommandParser

from Source.Core.Planner.engineering_tool_router import EngineeringToolRouter
from Source.Core.Fusion.visual_fusion import VisualFusionEngine
from Source.Core.Character.character_pipeline import CharacterGenerationPipeline
from Source.Core.Game.game_pipeline import GameGenerationPipeline
from Source.Core.Game.end_to_end_game_pipeline import EndToEndGamePipeline


class CommandPipeline:

    def __init__(self):
        self.parser = CommandParser()
        self.engineering_router = EngineeringToolRouter()

    def process(self, text: str):
        command = self.parser.parse(text)
        route = self.engineering_router.route(command)
        if route:
            command.metadata["engineering_route"] = route
        print(command.to_dict())
        return command

    def process_image(self, text: str, image_path: str, vision_client=None):
        """Parse a request and attach visual evidence plus Unity build commands."""
        command = self.parser.parse(text)
        fusion = VisualFusionEngine(vision_client=vision_client)
        return fusion.attach(command, image_path)

    def process_character_image(self, text: str, image_path: str, vision_client=None, name=None):
        command = self.parser.parse(text)
        pipeline = CharacterGenerationPipeline(vision_client=vision_client)
        return pipeline.attach(command, image_path, name)

    def process_game_request(self, text: str, name=None):
        """Convert a supported one-sentence game request into a staged Unity build plan."""
        command = self.parser.parse(text)
        return GameGenerationPipeline().attach(command, name)

    def process_game_from_image(self, text: str, image_path: str, vision_client=None, name=None):
        """Turn one reference image plus a game request into a Unity-ready build plan."""
        command = self.parser.parse(text)
        return EndToEndGamePipeline(vision_client=vision_client).attach(command, image_path, name)
