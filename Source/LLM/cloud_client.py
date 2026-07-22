"""Optional OpenAI-compatible cloud client. Secrets are supplied only at runtime."""

import base64
import json
from pathlib import Path
from typing import Any, Callable
from urllib.error import URLError
from urllib.request import Request, urlopen


class CloudCredentialsMissing(RuntimeError):
    pass


class CloudModelUnavailable(RuntimeError):
    pass


class OpenRouterClient:
    def __init__(self, model, api_key, endpoint="https://openrouter.ai/api/v1/chat/completions", transport: Callable[[str, dict[str, Any], dict[str, str]], dict[str, Any]] | None = None, timeout=90):
        if not api_key:
            raise CloudCredentialsMissing("Cloud mode requires OPENROUTER_API_KEY in the environment; the key is never stored in project files.")
        self.model, self.api_key, self.endpoint, self.timeout = model, api_key, endpoint, timeout
        self.transport = transport or self._transport

    def generate(self, prompt, task="chat", system=""):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self._complete(messages, task)

    def analyze_image(self, image_path, prompt):
        path = Path(image_path)
        mime = "image/png" if path.suffix.casefold() == ".png" else "image/jpeg"
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"}},
        ]
        return self._complete([{"role": "user", "content": content}], "vision")

    def _complete(self, messages, task):
        payload = {"model": self.model, "messages": messages, "temperature": 0}
        response = self.transport(self.endpoint, payload, {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise CloudModelUnavailable(f"Cloud model '{self.model}' returned no usable {task} response.") from error
        if not isinstance(content, str) or not content.strip():
            raise CloudModelUnavailable(f"Cloud model '{self.model}' returned empty {task} output.")
        return content.strip()

    def _transport(self, endpoint, payload, headers):
        request = Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, json.JSONDecodeError) as error:
            raise CloudModelUnavailable(f"Cloud model service is unavailable at {endpoint}.") from error
