"""Bounded Qwen Code CLI adapter for AI Engineer change-set generation.

Qwen Code is used only as a text/model provider here. Its file, shell, web and
sub-agent tools are disabled; the returned text still has to pass the normal
AI Engineer protocol validator before Unity can apply anything.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
from typing import Any, Callable


class QwenCodeUnavailable(RuntimeError):
    """Raised when the Qwen Code executable/provider cannot produce output."""


@dataclass(frozen=True)
class QwenCodeStatus:
    available: bool
    executable: str
    version: str
    provider: str
    model: str
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


Runner = Callable[[list[str], str, str, int, dict[str, str]], tuple[int, str, str]]


class QwenCodeClient:
    """Invoke Qwen Code headlessly without granting it workspace mutation tools."""

    def __init__(
        self,
        executable: str = "qwen",
        model: str = "qwen3:30b",
        base_url: str = "http://127.0.0.1:11434/v1",
        auth_type: str = "openai",
        api_key: str = "ollama",
        working_directory: str = "",
        timeout: int = 240,
        prefer_account: bool = True,
        require_account: bool = False,
        network_checker: Callable[[], bool] | None = None,
        runner: Runner | None = None,
    ):
        self.executable = executable or "qwen"
        self.model = model
        self.base_url = base_url
        self.auth_type = auth_type or "openai"
        self.api_key = api_key
        self.working_directory = working_directory or os.getcwd()
        self.timeout = max(30, int(timeout))
        self.prefer_account = prefer_account
        self.require_account = require_account
        self.network_checker = network_checker or self._internet_available
        self.runner = runner or self._run
        self.qwen_home = Path(__file__).resolve().parents[2] / ".runtime" / "qwen"

    def generate(self, prompt: str, system: str = "", task: str = "chat") -> str:
        executable = self._resolved_executable()
        if not executable:
            raise QwenCodeUnavailable(
                "Qwen Code is not installed or is not on PATH. Install the official CLI, then restart Unity."
            )

        full_prompt = "\n\n".join(part for part in (system.strip(), f"TASK ({task}):\n{prompt.strip()}") if part)
        if self.require_account:
            if not self._has_user_provider():
                raise QwenCodeUnavailable("Qwen Code account/provider is not configured. Open the Qwen terminal and run /auth.")
            if not self.network_checker():
                raise QwenCodeUnavailable("Internet is unavailable; Qwen account execution is suspended.")
            code, stdout, stderr = self._invoke(executable, full_prompt, account=True)
            if code != 0:
                detail = (stderr or stdout).strip()[-1600:]
                raise QwenCodeUnavailable(f"Qwen Code account execution failed: {detail}".strip())
            return self._extract_response(stdout)
        if self.prefer_account and self._has_user_provider() and self.network_checker():
            code, stdout, _ = self._invoke(executable, full_prompt, account=True)
            if code == 0 and stdout.strip():
                try:
                    return self._extract_response(stdout)
                except QwenCodeUnavailable:
                    pass

        code, stdout, stderr = self._invoke(executable, full_prompt, account=False)
        if code != 0:
            detail = (stderr or stdout).strip()[-1600:]
            raise QwenCodeUnavailable(f"Qwen Code exited with code {code}. {detail}".strip())
        return self._extract_response(stdout)

    def _invoke(self, executable: str, full_prompt: str, account: bool) -> tuple[int, str, str]:
        args = [
            executable,
            "-p", "Read the complete task from standard input. Return only the requested final answer.",
            "--output-format", "json",
            "--safe-mode",
            "--approval-mode", "plan",
            "--exclude-tools", "shell,write,edit,agent,web_fetch,web_search",
            "--max-tool-calls", "25",
            "--max-session-turns", "4",
            "--max-wall-time", f"{self.timeout}s",
        ]
        if not account and self.auth_type:
            args.extend(("--auth-type", self.auth_type))
        if not account and self.model:
            args.extend(("--model", self.model))

        environment = os.environ.copy()
        self.qwen_home.mkdir(parents=True, exist_ok=True)
        runtime_directory = self.qwen_home / "runtime"
        runtime_directory.mkdir(parents=True, exist_ok=True)
        environment["QWEN_HOME"] = str(self.qwen_home)
        environment["QWEN_RUNTIME_DIR"] = str(runtime_directory)
        environment["QWEN_CODE_SAFE_MODE"] = "true"
        environment["QWEN_CODE_DISABLE_CRON"] = "1"
        if not account and self.base_url:
            environment["OPENAI_BASE_URL"] = self.base_url
        if not account and self.model:
            environment["OPENAI_MODEL"] = self.model
        if not account and self.api_key:
            environment["OPENAI_API_KEY"] = self.api_key

        try:
            return self.runner(args, full_prompt, self.working_directory, self.timeout, environment)
        except (OSError, subprocess.SubprocessError) as error:
            raise QwenCodeUnavailable(f"Qwen Code could not be started: {error}") from error

    def status(self) -> QwenCodeStatus:
        executable = self._resolved_executable()
        account_configured = self._has_user_provider()
        provider = "account-required" if self.require_account else ("account-first/local-fallback" if self.prefer_account and account_configured else ("local-ollama" if self._is_local_ollama() else self.auth_type))
        if not executable:
            return QwenCodeStatus(False, self.executable, "", provider, self.model, "Qwen Code CLI is not installed.")
        version = ""
        try:
            code, stdout, stderr = self.runner([executable, "--version"], "", self.working_directory, 15, os.environ.copy())
            if code == 0:
                version = stdout.strip().splitlines()[-1] if stdout.strip() else "installed"
            else:
                version = (stderr or "installed").strip().splitlines()[-1]
        except (OSError, subprocess.SubprocessError):
            version = "installed"
        if self.require_account:
            message = "Account-only mutation mode. Local model fallback is disabled."
        elif self.prefer_account and account_configured:
            message = "User provider is preferred online; local Ollama is the automatic fallback."
        else:
            message = "Uses local Ollama without an API key." if self._is_local_ollama() else "Provider credentials are read at runtime."
        return QwenCodeStatus(True, executable, version, provider, self.model, message)

    def _resolved_executable(self) -> str:
        candidate = Path(self.executable).expanduser()
        if candidate.is_file():
            return str(candidate.resolve())
        found = shutil.which(self.executable)
        if found:
            return found
        bundled = Path(__file__).resolve().parents[2] / "Tools" / "QwenCode" / "bin" / ("qwen.cmd" if os.name == "nt" else "qwen")
        return str(bundled) if bundled.is_file() else ""

    def _is_local_ollama(self) -> bool:
        return "127.0.0.1:11434" in self.base_url or "localhost:11434" in self.base_url

    def _has_user_provider(self) -> bool:
        for settings in (self.qwen_home / "settings.json",):
            if not settings.is_file():
                continue
            try:
                payload = json.loads(settings.read_text(encoding="utf-8-sig"))
                selected = payload.get("security", {}).get("auth", {}).get("selectedType", "")
                if selected or payload.get("modelProviders"):
                    return True
            except (OSError, json.JSONDecodeError, AttributeError):
                continue
        return False

    @staticmethod
    def _internet_available() -> bool:
        try:
            with socket.create_connection(("qwen.ai", 443), timeout=3):
                return True
        except OSError:
            return False

    @staticmethod
    def _extract_response(stdout: str) -> str:
        text = (stdout or "").strip()
        if not text:
            raise QwenCodeUnavailable("Qwen Code returned no output.")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return text

        if isinstance(payload, dict):
            if payload.get("protocol") and payload.get("operations"):
                return json.dumps(payload, ensure_ascii=False)
            for key in ("response", "result", "output"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        if isinstance(payload, list):
            for item in reversed(payload):
                if not isinstance(item, dict):
                    continue
                value = item.get("result") or item.get("response")
                if isinstance(value, str) and value.strip():
                    return value.strip()
            chunks = []
            for item in payload:
                message = item.get("message", {}) if isinstance(item, dict) else {}
                for content in message.get("content", []) if isinstance(message, dict) else []:
                    if isinstance(content, dict) and content.get("type") == "text" and content.get("text"):
                        chunks.append(str(content["text"]))
            if chunks:
                return "\n".join(chunks).strip()
        raise QwenCodeUnavailable("Qwen Code JSON output did not contain an assistant result.")

    @staticmethod
    def _run(args: list[str], input_text: str, cwd: str, timeout: int, environment: dict[str, str]) -> tuple[int, str, str]:
        result = subprocess.run(
            args,
            input=input_text,
            cwd=cwd if Path(cwd).is_dir() else None,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout + 10,
            check=False,
        )
        return result.returncode, result.stdout, result.stderr
