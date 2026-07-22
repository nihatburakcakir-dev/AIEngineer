from Source.Core.Tools.Builtin.bug_detector_tool import BugDetectorTool
from Source.Core.Tools.Builtin.dead_code_tool import DeadCodeTool
from Source.Core.Tools.Builtin.performance_tool import PerformanceTool
from Source.Core.Tools.Builtin.refactor_tool import RefactorTool


def register_engineering_tools(registry):
    """Register all FAZ 4 tools in a single, repeatable place."""
    for tool in (RefactorTool(), BugDetectorTool(), PerformanceTool(), DeadCodeTool()):
        registry.register(tool)
    return registry
