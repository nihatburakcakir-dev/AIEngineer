from Source.Core.Bootstrap.container import Container

from Source.Core.Tools.registry import ToolRegistry

from Source.Brain.orchestrator import Orchestrator
from Source.Core.Tools.engineering_registry import register_engineering_tools


class Bootstrap:

    def __init__(self):

        self.container = Container()

        self.registry = ToolRegistry()

    def build(self):

        self._register_services()

        self._register_tools()

        return Orchestrator(

            self.registry

        )

    def _register_services(self):

        pass

    def _register_tools(self):
        register_engineering_tools(self.registry)
