from Source.LLM.llm_client import LocalLLMRouter


class LLMClient:
    """Backward-compatible facade; all requests remain local Ollama requests."""

    def __init__(self, config=None, router=None):
        self.router = router or LocalLLMRouter(config)

    def generate(self, prompt: str, task="chat", system=""):
        return self.router.generate(prompt, task=task, system=system)
