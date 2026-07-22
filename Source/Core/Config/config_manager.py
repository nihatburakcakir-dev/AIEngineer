import json

class ConfigManager:

    def __init__(self, config_file="ai_config.json"):

        with open(
            config_file,
            encoding="utf-8-sig"
        ) as f:

            self.config = json.load(f)

    @property
    def project_root(self):

        return self.config["project_root"]

    @property
    def backup_folder(self):

        return self.config.get(
            "backup_folder",
            "Backups"
        )

    @property
    def auto_backup(self):

        return self.config.get(
            "auto_backup",
            True
        )

    @property
    def compile_after_patch(self):

        return self.config.get(
            "compile_after_patch",
            True
        )

    @property
    def rollback_on_error(self):

        return self.config.get(
            "rollback_on_error",
            True
        )

    @property
    def vision_model(self):
        return self.config.get("vision_model", "llava:7b")

    @property
    def vision_endpoint(self):
        return self.config.get("vision_endpoint", "http://127.0.0.1:11434/api/chat")

    @property
    def ollama_endpoint(self):
        return self.config.get("ollama_endpoint", "http://127.0.0.1:11434/api/chat")

    @property
    def local_only(self):
        return bool(self.config.get("local_only", True))

    @property
    def model_routes(self):
        defaults = {
            "chat": self.config.get("text_model", "qwen3:30b"),
            "planning": self.config.get("text_model", "qwen3:30b"),
            "code_generation": self.config.get("text_model", "qwen3:30b"),
            "vision": self.vision_model,
        }
        defaults.update(self.config.get("model_routes", {}))
        return defaults

    def model_for(self, task):
        return self.model_routes.get(task, self.model_routes["chat"])

    @property
    def cloud_provider(self):
        return self.config.get("cloud_provider", "openrouter")

    @property
    def cloud_endpoint(self):
        return self.config.get("cloud_endpoint", "https://openrouter.ai/api/v1/chat/completions")

    @property
    def cloud_api_key_env(self):
        return self.config.get("cloud_api_key_env", "OPENROUTER_API_KEY")

    @property
    def cloud_api_key(self):
        import os
        return os.environ.get(self.cloud_api_key_env, "")

    @property
    def cloud_enabled(self):
        return bool(self.cloud_optional and self.cloud_api_key)

    @property
    def cloud_optional(self):
        return bool(self.config.get("cloud_optional", True))

    @property
    def cloud_model_routes(self):
        defaults = {"chat": "openrouter/free", "planning": "openrouter/free", "code_generation": "openrouter/free", "vision": "openrouter/free"}
        defaults.update(self.config.get("cloud_model_routes", {}))
        return defaults

    def cloud_model_for(self, task):
        return self.cloud_model_routes.get(task, self.cloud_model_routes["chat"])

    @property
    def qwen_code_executable(self):
        import os
        return os.environ.get("AIENGINEER_QWEN_EXECUTABLE", "") or self.config.get("qwen_code_executable", "qwen")

    @property
    def qwen_code_model(self):
        return self.config.get("qwen_code_model", self.model_for("code_generation"))

    @property
    def qwen_code_base_url(self):
        return self.config.get("qwen_code_base_url", "http://127.0.0.1:11434/v1")

    @property
    def qwen_code_auth_type(self):
        return self.config.get("qwen_code_auth_type", "openai")

    @property
    def qwen_code_api_key_env(self):
        return self.config.get("qwen_code_api_key_env", "QWEN_CODE_API_KEY")

    @property
    def qwen_code_api_key(self):
        import os
        configured = os.environ.get(self.qwen_code_api_key_env, "")
        if configured:
            return configured
        if "127.0.0.1:11434" in self.qwen_code_base_url or "localhost:11434" in self.qwen_code_base_url:
            return "ollama"
        return ""

    @property
    def qwen_code_timeout(self):
        return int(self.config.get("qwen_code_timeout", 240))

    @property
    def codex_executable(self):
        import os
        return os.environ.get("AIENGINEER_CODEX_EXECUTABLE", "") or self.config.get("codex_executable", "codex")

    @property
    def codex_model(self):
        return self.config.get("codex_model", "")

    @property
    def codex_timeout(self):
        return int(self.config.get("codex_timeout", 300))
