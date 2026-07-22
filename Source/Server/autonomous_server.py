"""Local HTTP bridge between Unity and the autonomous AI Engineer backend."""

from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import sys
import traceback

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from Source.Core.Config.config_manager import ConfigManager
from Source.Core.Models.change_protocol import ALLOWED_KINDS, PROTOCOL, ProtocolError
from Source.Core.Planner.autonomous_change_planner import AutonomousChangePlanner
from Source.Knowledge.importer import Importer
from Source.LLM.ollama_client import LocalModelUnavailable, OllamaClient
from Source.LLM.codex_cli_client import CodexCliClient, CodexCliUnavailable
from Source.LLM.llm_client import AccountProviderUnavailable
from Source.LLM.qwen_code_client import QwenCodeClient, QwenCodeUnavailable
from Source.Project.importer import ProjectImporter


_brain = None
_planner = None
importer = Importer()
project_importer = ProjectImporter()


def planner():
    global _planner
    if _planner is None:
        _planner = AutonomousChangePlanner()
    return _planner


def legacy_brain():
    global _brain
    if _brain is None:
        from Source.Brain.brain import Brain
        _brain = Brain()
    return _brain


class Handler(BaseHTTPRequestHandler):
    server_version = "AIEngineer/1.0"

    def log_message(self, format, *args):
        print("[HTTP] " + (format % args))

    def do_GET(self):
        if self.path == "/health":
            self._health()
            return
        if self.path == "/v1/capabilities":
            self._json(200, {
                "protocol": PROTOCOL,
                "operations": sorted(ALLOWED_KINDS),
                "autonomousRepair": True,
                "rollback": "unity-transaction",
                "localFirst": True,
                "modelModes": ["local", "qwen_code", "codex", "cloud-opt-in"],
                "vision": ["local", "qwen-code-uses-local-vision", "codex-uses-local-vision", "cloud-opt-in"],
            })
            return
        self._json(404, {"error": "not_found", "message": "Unknown endpoint."})

    def do_POST(self):
        try:
            data = self._request_json()
            if self.path == "/v1/plan":
                self._json(200, planner().plan(data).to_dict())
                return
            if self.path == "/v1/repair":
                self._json(200, planner().repair(data).to_dict())
                return
            if self.path in {"/", "/v1/legacy-plan"}:
                self._legacy_plan(data)
                return
            self._json(404, {"error": "not_found", "message": "Unknown endpoint."})
        except (ProtocolError, ValueError, FileNotFoundError) as error:
            print("[PLAN REJECTED] " + str(error))
            self._json(400, {"error": "invalid_request", "message": str(error)})
        except (LocalModelUnavailable, QwenCodeUnavailable, CodexCliUnavailable, AccountProviderUnavailable) as error:
            print("[MODEL UNAVAILABLE] " + str(error))
            self._json(503, {"error": "model_unavailable", "message": str(error)})
        except Exception as error:
            traceback.print_exc()
            self._json(500, {"error": "internal_error", "message": str(error)})

    def _legacy_plan(self, data):
        if "objects" in data:
            importer.import_scene(data["objects"])
        if "project" in data:
            project_importer.import_project(data["project"])
        tasks = legacy_brain().think(data["prompt"])
        self._json(200, {
            "workflow": "AI Workflow",
            "tasks": [{"action": task.action, "target": task.target} for task in tasks],
        })

    def _health(self):
        config = ConfigManager()
        client = OllamaClient(model=config.model_for("code_generation"), endpoint=config.ollama_endpoint, timeout=3)
        status = client.status()
        qwen_status = QwenCodeClient(
            executable=config.qwen_code_executable,
            model=config.qwen_code_model,
            base_url=config.qwen_code_base_url,
            auth_type=config.qwen_code_auth_type,
            api_key=config.qwen_code_api_key,
            working_directory=config.project_root,
            timeout=config.qwen_code_timeout,
        ).status()
        codex_status = CodexCliClient(
            executable=config.codex_executable,
            model=config.codex_model,
            working_directory=config.project_root,
            timeout=config.codex_timeout,
        ).status()
        self._json(200, {
            "status": "ok", "protocol": PROTOCOL, "backend": "autonomous-change-set",
            "localModel": asdict(status), "qwenCode": qwen_status.to_dict(),
            "codex": codex_status.to_dict(), "cloudEnabled": config.cloud_enabled,
        })

    def _request_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 10_000_000:
            raise ValueError("Request body is empty or too large.")
        data = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Request JSON must be an object.")
        return data

    def _json(self, status, payload):
        response = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)


def run():
    # A long model inference must not block Control Center health checks or a
    # cancellation/retry request. Request handlers remain local-only.
    server = ThreadingHTTPServer(("127.0.0.1", 8080), Handler)
    print()
    print("=" * 60)
    print("AI ENGINE SERVER")
    print("=" * 60)
    print("Listening : http://127.0.0.1:8080")
    print("Protocol  : " + PROTOCOL)
    print()
    server.serve_forever()


if __name__ == "__main__":
    run()
