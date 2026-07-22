"""Command-to-game-plan bridge for the Phase 7 multi-system workflow."""

from Source.Core.Game.project_scaffolder import ProjectScaffolder
from Source.Core.Game.reference_game_input import ReferenceGameLibrary


class GameGenerationPipeline:
    def __init__(self, library=None, scaffolder=None):
        self.library = library or ReferenceGameLibrary()
        self.scaffolder = scaffolder or ProjectScaffolder()

    def plan(self, prompt: str, name: str | None = None):
        template = self.library.resolve(prompt)
        return self.scaffolder.build_plan(template, name)

    def attach(self, command, name: str | None = None):
        plan = self.plan(command.prompt, name)
        command.intent = "BUILD_GAME_PROTOTYPE"
        command.target = plan.game_name
        command.metadata["game_scaffold_plan"] = plan.to_dict()
        command.metadata["game_build_request"] = self.scaffolder.build_request(plan)
        return command
