import json
import tempfile
import unittest
from pathlib import Path

from Source.Core.Config.config_manager import ConfigManager
from Source.LLM.llm_client import LocalLLMRouter
from Source.LLM.cloud_client import CloudCredentialsMissing, OpenRouterClient
from Source.LLM.local_benchmark import LocalBenchmark
from Source.LLM.model_policy import ModelPolicy
from Source.LLM.ollama_client import LocalModelUnavailable, OllamaClient


class LocalOperationTests(unittest.TestCase):
    def test_config_routes_text_and_vision_tasks_to_local_models(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.json"
            config_path.write_text(json.dumps({"project_root": "C:/Project", "local_only": True, "text_model": "code-local", "vision_model": "vision-local", "model_routes": {"planning": "planner-local"}}), encoding="utf-8")
            config = ConfigManager(config_path)
        self.assertTrue(config.local_only)
        self.assertEqual(config.model_for("planning"), "planner-local")
        self.assertEqual(config.model_for("code_generation"), "code-local")
        self.assertEqual(config.model_for("vision"), "vision-local")

    def test_ollama_client_sends_a_local_chat_request_and_returns_text(self):
        captured = {}
        def transport(endpoint, payload):
            captured["endpoint"], captured["payload"] = endpoint, payload
            return {"message": {"content": "local answer"}}
        answer = OllamaClient("qwen-local", "http://127.0.0.1:11434/api/chat", transport=transport).generate("plan a patch", task="planning")
        self.assertEqual(answer, "local answer")
        self.assertEqual(captured["payload"]["model"], "qwen-local")
        self.assertFalse(captured["payload"]["stream"])

    def test_unavailable_local_service_has_a_clear_no_cloud_error(self):
        def unavailable(endpoint, payload):
            raise LocalModelUnavailable("offline")
        status = OllamaClient("qwen-local", transport=unavailable).status()
        self.assertFalse(status.available)
        self.assertIn("offline", status.message)

    def test_router_selects_the_model_for_each_local_task(self):
        class Config:
            local_only = True
            ollama_endpoint = "http://local/api/chat"
            def model_for(self, task): return {"planning": "planner", "code_generation": "coder"}.get(task, "chat")
        seen = []
        class Stub:
            def __init__(self, model, endpoint): seen.append((model, endpoint))
            def generate(self, prompt, system="", task="chat"): return f"{task}:{prompt}"
        router = LocalLLMRouter(Config(), Stub)
        self.assertEqual(router.generate("make code", task="code_generation"), "code_generation:make code")
        self.assertEqual(seen, [("coder", "http://local/api/chat")])

    def test_policy_keeps_all_standard_tasks_local_and_cloud_opt_in(self):
        class Config:
            local_only = True
            cloud_optional = True
            def model_for(self, task): return {"vision": "vision-local"}.get(task, "text-local")
        policies = ModelPolicy(Config()).all()
        self.assertEqual({policy.task for policy in policies}, {"chat", "planning", "code_generation", "vision"})
        self.assertTrue(all(policy.execution == "local" for policy in policies))
        self.assertTrue(all(policy.cloud_fallback == "explicitly-configured-only" for policy in policies))

    def test_benchmark_records_success_and_elapsed_time_without_cloud(self):
        class Client:
            model = "local-test"
            def generate(self, prompt, task): return "LOCAL_BENCHMARK_OK"
        result = LocalBenchmark().text(Client())
        self.assertTrue(result.success)
        self.assertEqual(result.model, "local-test")
        self.assertGreaterEqual(result.elapsed_seconds, 0)

    def test_cloud_client_needs_a_runtime_key_and_uses_openai_compatible_payload(self):
        with self.assertRaises(CloudCredentialsMissing):
            OpenRouterClient("openrouter/free", "")
        captured = {}
        def transport(endpoint, payload, headers):
            captured.update(endpoint=endpoint, payload=payload, headers=headers)
            return {"choices": [{"message": {"content": "cloud answer"}}]}
        client = OpenRouterClient("openrouter/free", "secret", transport=transport)
        self.assertEqual(client.generate("hello", task="planning"), "cloud answer")
        self.assertEqual(captured["payload"]["model"], "openrouter/free")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer secret")

    def test_router_allows_explicit_cloud_mode_without_changing_the_local_default(self):
        class Config:
            ollama_endpoint = "http://local/api/chat"
            cloud_endpoint = "https://cloud/chat"
            cloud_api_key = "key"
            def model_for(self, task): return "local-model"
            def cloud_model_for(self, task): return "cloud-model"
        seen = []
        class Cloud:
            def __init__(self, model, api_key, endpoint): seen.append((model, api_key, endpoint))
            def generate(self, prompt, system="", task="chat"): return "cloud"
        router = LocalLLMRouter(Config(), client_factory=lambda **_: None, cloud_factory=Cloud)
        self.assertEqual(router.generate("x", mode="cloud"), "cloud")
        self.assertEqual(seen, [("cloud-model", "key", "https://cloud/chat")])


if __name__ == "__main__":
    unittest.main()
