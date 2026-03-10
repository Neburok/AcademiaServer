"""
claude_provider.py — Proveedor de IA usando Anthropic Claude API.

Implementa el contrato AIProvider con la API de Anthropic (mensajes v1).
Soporta modo 'cloud' y como fallback en modo 'hybrid'.

Diferencias clave con CloudProvider (OpenAI):
- Endpoint: POST /v1/messages (no /chat/completions)
- Auth: x-api-key (no Authorization: Bearer)
- System prompt: parámetro separado (no en messages[0])
- max_tokens: obligatorio (no opcional)
- Respuesta: data["content"][0]["text"] (no choices[0].message.content)
- JSON: via prompt engineering + extracción regex (no response_format)
"""

import json
import re
import time

import requests

from academiaserver.ai.prompts import build_user_message, get_system_prompt
from academiaserver.ai.provider import AIProvider


class ClaudeProvider(AIProvider):
    """Proveedor de IA usando Anthropic Claude API (v1/messages)."""

    ANTHROPIC_VERSION = "2023-06-01"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        chat_model: str,
        timeout_seconds: int = 25,
        http_max_retries: int = 2,
        http_retry_delay_seconds: int = 1,
        max_tokens: int = 1024,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.chat_model = chat_model
        self.timeout_seconds = timeout_seconds
        self.http_max_retries = max(1, http_max_retries)
        self.http_retry_delay_seconds = max(0, http_retry_delay_seconds)
        self.max_tokens = max_tokens

    def analyze_message(
        self,
        text: str,
        context: list[str] = [],
        memory: list[dict] = [],
        system_prompt_override: str | None = None,
    ) -> dict:
        """Envía un mensaje a Claude API y retorna el análisis como dict.

        Args:
            text: Mensaje del usuario a analizar.
            context: Últimos turnos de conversación (contexto).
            memory: Notas relevantes del historial (memoria RAG).
            system_prompt_override: System prompt alternativo (agentes educativos).

        Returns:
            Dict validado con el análisis de la nota.

        Raises:
            RuntimeError: Si ANTHROPIC_API_KEY no está configurada.
            ValueError: Si la respuesta no contiene JSON válido.
            requests.RequestException: Si todos los intentos HTTP fallan.
        """
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY no configurada")

        url = f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.ANTHROPIC_VERSION,
            "Content-Type": "application/json",
        }
        system = system_prompt_override if system_prompt_override else get_system_prompt()
        payload = {
            "model": self.chat_model,
            "max_tokens": self.max_tokens,
            "system": system,  # ← parámetro separado, no dentro de messages
            "messages": [
                {"role": "user", "content": build_user_message(text, context, memory)},
            ],
        }

        # Loop de reintentos — lógica idéntica a CloudProvider
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
            raise RuntimeError("No fue posible obtener respuesta de Claude API")

        data = response.json()
        content_blocks = data.get("content", [])
        if not content_blocks:
            raise ValueError("Claude API: respuesta sin bloques de contenido")

        text_content = content_blocks[0].get("text", "").strip()
        if not text_content:
            raise ValueError("Claude API: bloque de texto vacío")

        return _parse_json_response(text_content)


def _parse_json_response(text: str) -> dict:
    """Parsea JSON desde el texto de respuesta de Claude.

    Claude no tiene 'response_format: json_object' como OpenAI, así que
    el modelo puede incluir texto antes/después del JSON. Este helper
    intenta un parse directo y, si falla, extrae el primer bloque {...}.

    Args:
        text: Texto de respuesta de Claude.

    Returns:
        Dict parseado desde el JSON.

    Raises:
        ValueError: Si no se encuentra JSON válido en el texto.
    """
    # Intento 1: JSON directo (el modelo sigue bien las instrucciones)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Intento 2: extraer el primer bloque {...} con regex
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Claude API: no se encontró JSON válido en la respuesta: {text[:200]!r}")
