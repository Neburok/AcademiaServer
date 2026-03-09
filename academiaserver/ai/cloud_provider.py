import json
import time

import requests

from academiaserver.ai.prompts import build_user_message, get_system_prompt
from academiaserver.ai.provider import AIProvider


class CloudProvider(AIProvider):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        chat_model: str,
        timeout_seconds: int = 25,
        http_max_retries: int = 2,
        http_retry_delay_seconds: int = 1,
    ):
        self.api_key = api_key
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
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY no configurada")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        system = system_prompt_override if system_prompt_override else get_system_prompt()
        payload = {
            "model": self.chat_model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": build_user_message(text, context, memory)},
            ],
        }

        response = None
        for attempt in range(1, self.http_max_retries + 1):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                break
            except requests.RequestException:
                if attempt == self.http_max_retries:
                    raise
                time.sleep(self.http_retry_delay_seconds)

        if response is None:
            raise RuntimeError("No fue posible obtener respuesta de proveedor cloud")

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise ValueError("Proveedor cloud sin choices")
        content = choices[0].get("message", {}).get("content", "").strip()
        if not content:
            raise ValueError("Proveedor cloud sin contenido")
        return json.loads(content)
