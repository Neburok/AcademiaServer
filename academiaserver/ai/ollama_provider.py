import json
import time

import requests

from academiaserver.ai.prompts import build_user_message, get_system_prompt
from academiaserver.ai.provider import AIProvider


class OllamaProvider(AIProvider):
    def __init__(
        self,
        base_url: str,
        chat_model: str,
        timeout_seconds: int = 25,
        http_max_retries: int = 2,
        http_retry_delay_seconds: int = 1,
    ):
        self.base_url = base_url.rstrip("/")
        self.chat_model = chat_model
        self.timeout_seconds = timeout_seconds
        self.http_max_retries = max(1, http_max_retries)
        self.http_retry_delay_seconds = max(0, http_retry_delay_seconds)

    def analyze_message(
        self,
        text: str,
        context: list[str] = [],
        memory: list[dict] = [],
        system_prompt_override: str | None = None,
    ) -> dict:
        url = f"{self.base_url}/api/chat"
        system = system_prompt_override if system_prompt_override else get_system_prompt()
        payload = {
            "model": self.chat_model,
            "format": "json",
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": build_user_message(text, context, memory)},
            ],
        }

        response = None
        last_error = None
        for attempt in range(1, self.http_max_retries + 1):
            try:
                response = requests.post(url, json=payload, timeout=self.timeout_seconds)
                response.raise_for_status()
                break
            except requests.RequestException as exc:
                last_error = exc
                if attempt == self.http_max_retries:
                    raise
                time.sleep(self.http_retry_delay_seconds)

        if response is None:
            raise RuntimeError(f"Fallo al conectar con Ollama: {last_error}")

        data = response.json()
        content = data.get("message", {}).get("content", "").strip()
        if not content:
            raise ValueError("Ollama no devolvio contenido para analisis")

        parsed = json.loads(content)
        return parsed
