"""Read-only Codex CLI provider backed by a user's ChatGPT or API login.

Codex may inspect the Unity workspace, but it returns an AI Engineer change-set
instead of editing directly. Unity remains the only writer and therefore keeps
transaction snapshots, compile repair and rollback guarantees intact.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import os
from pathlib import Path
import shutil
import socket
import subprocess
from typing import Any, Callable


class CodexCliUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class CodexCliStatus:
    available: bool
    authenticated: bool
    executable: str
    version: str
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


Runner = Callable[[list[str], str, str, int, dict[str, str]], tuple[int, str, str]]


class CodexCliClient:
    """Use `codex exec` in read-only/ephemeral mode as a manifest generator."""

    def __init__(
        self,
        executable: str = "codex",
        model: str = "",
        working_directory: str = "",
        timeout: int = 300,
        network_checker: Callable[[], bool] | None = None,
        runner: Runner | None = None,
    ):
        self.executable = executable or "codex"
        self.model = model
        self.working_directory = working_directory or os.getcwd()
        self.timeout = max(30, int(timeout))
        self.network_checker = network_checker or self._internet_available
        self.runner = runner or self._run

    def generate(self, prompt: str, system: str = "", task: str = "chat") -> str:
        executable = self._resolved_executable()
        if not executable:
            raise CodexCliUnavailable(
                "Codex CLI is not installed. Install the official CLI and run 'codex login' with your ChatGPT account."
            )
        if not self.network_checker():
            raise CodexCliUnavailable("Internet is unavailable; switching to the local model.")
        full_prompt = "\n\n".join(part for part in (system.strip(), f"TASK ({task}):\n{prompt.strip()}") if part)
        args = [
            executable,
            "exec",
            "--ephemeral",
            "--sandbox", "read-only",
            "--ask-for-approval", "never",
            "--skip-git-repo-check",
        ]
        if self.model:
            args.extend(("--model", self.model))
        args.append("Read the complete task supplied on standard input. Inspect project files only when useful. Return only the requested final answer and do not edit files.")
        try:
            code, stdout, stderr = self.runner(args, full_prompt, self.working_directory, self.timeout, os.environ.copy())
        except (OSError, subprocess.SubprocessError) as error:
            raise CodexCliUnavailable(f"Codex CLI could not be started: {error}") from error
        if code != 0:
            detail = (stderr or stdout).strip()[-1600:]
            raise CodexCliUnavailable(f"Codex CLI exited with code {code}. {detail}".strip())
        output = stdout.strip()
        if not output:
            raise CodexCliUnavailable("Codex CLI returned no final message.")
        return output

    def status(self) -> CodexCliStatus:
        executable = self._resolved_executable()
        if not executable:
            return CodexCliStatus(False, False, self.executable, "", "Codex CLI is not installed.")
        version = "installed"
        authenticated = False
        message = "Run 'codex login' and sign in with ChatGPT."
        try:
            code, stdout, _ = self.runner([executable, "--version"], "", self.working_directory, 15, os.environ.copy())
            if code == 0 and stdout.strip():
                version = stdout.strip().splitlines()[-1]
            login_code, login_out, login_err = self.runner(
                [executable, "login", "status"], "", self.working_directory, 20, os.environ.copy()
            )
            authenticated = login_code == 0
            if authenticated:
                message = (login_out or "ChatGPT/Codex login is active.").strip().splitlines()[-1]
            elif login_err.strip():
                message = login_err.strip().splitlines()[-1]
        except (OSError, subprocess.SubprocessError):
            pass
        return CodexCliStatus(True, authenticated, executable, version, message)

    def _resolved_executable(self) -> str:
        candidate = Path(self.executable).expanduser()
        if candidate.is_file():
            return str(candidate.resolve())
        if os.name == "nt":
            local = os.environ.get("LOCALAPPDATA", "")
            standalone = Path(local) / "Programs" / "OpenAI" / "Codex" / "bin" / "codex.exe"
            if standalone.is_file():
                return str(standalone)
        return shutil.which(self.executable) or ""

    @staticmethod
    def _internet_available() -> bool:
        try:
            with socket.create_connection(("chatgpt.com", 443), timeout=3):
                return True
        except OSError:
            return False

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
