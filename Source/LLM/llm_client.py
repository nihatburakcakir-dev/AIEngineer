"""Task-aware, local-only LLM facade."""

from Source.Core.Config.config_manager import ConfigManager
from Source.LLM.cloud_client import OpenRouterClient
from Source.LLM.codex_cli_client import CodexCliClient, CodexCliUnavailable
from Source.LLM.ollama_client import OllamaClient
from Source.LLM.qwen_code_client import QwenCodeClient, QwenCodeUnavailable


class AccountProviderUnavailable(RuntimeError):
    """Neither configured account provider can safely perform a mutation."""


class AccountFailoverClient:
    """Use Qwen/Codex accounts for mutations and never fall back to local writes."""

    def __init__(self, *providers):
        self.providers = providers
        self.last_provider = ""

    def generate(self, prompt, task="chat", system=""):
        errors = []
        for provider in self.providers:
            try:
                result = provider.generate(prompt, task=task, system=system)
                self.last_provider = type(provider).__name__
                return result
            except (QwenCodeUnavailable, CodexCliUnavailable) as error:
                errors.append(str(error))
        raise AccountProviderUnavailable("No account-backed provider is available. " + " | ".join(errors))


class LocalLLMRouter:
    def __init__(self, config=None, client_factory=None, cloud_factory=None, qwen_code_factory=None, codex_factory=None):
        self.config = config or ConfigManager()
        self.client_factory = client_factory or OllamaClient
        self.cloud_factory = cloud_factory or OpenRouterClient
        self.qwen_code_factory = qwen_code_factory or QwenCodeClient
        self.codex_factory = codex_factory or CodexCliClient

    def client_for(self, task="chat", mode="local"):
        if mode == "local":
            return self.client_factory(model=self.config.model_for(task), endpoint=self.config.ollama_endpoint)
        if mode == "cloud":
            return self.cloud_factory(model=self.config.cloud_model_for(task), api_key=self.config.cloud_api_key, endpoint=self.config.cloud_endpoint)
        if mode == "qwen_code":
            qwen = self.qwen_code_factory(
                executable=self.config.qwen_code_executable,
                model=self.config.qwen_code_model,
                base_url=self.config.qwen_code_base_url,
                auth_type=self.config.qwen_code_auth_type,
                api_key=self.config.qwen_code_api_key,
                working_directory=self.config.project_root,
                timeout=self.config.qwen_code_timeout,
                require_account=True,
            )
            codex = self.codex_factory(
                executable=self.config.codex_executable, model=self.config.codex_model,
                working_directory=self.config.project_root, timeout=self.config.codex_timeout,
            )
            return AccountFailoverClient(qwen, codex)
        if mode == "codex":
            codex = self.codex_factory(
                executable=self.config.codex_executable,
                model=self.config.codex_model,
                working_directory=self.config.project_root,
                timeout=self.config.codex_timeout,
            )
            qwen = self.qwen_code_factory(
                executable=self.config.qwen_code_executable, model=self.config.qwen_code_model,
                base_url=self.config.qwen_code_base_url, auth_type=self.config.qwen_code_auth_type,
                api_key=self.config.qwen_code_api_key, working_directory=self.config.project_root,
                timeout=self.config.qwen_code_timeout, require_account=True,
            )
            return AccountFailoverClient(codex, qwen)
        raise ValueError("Model mode must be 'local', 'qwen_code', 'codex' or 'cloud'.")

    def generate(self, prompt, task="chat", system="", mode="local"):
        return self.client_for(task, mode=mode).generate(prompt, system=system, task=task)
