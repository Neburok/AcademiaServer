"""
tests/test_claude_provider.py — Tests para ClaudeProvider.

Todos los tests usan mock HTTP (unittest.mock.patch) — sin llamadas reales
a la API de Anthropic. Se verifica el comportamiento del proveedor en
condiciones normales y de error.
"""

import json
import unittest
from unittest.mock import MagicMock, call, patch

import requests

from academiaserver.ai.claude_provider import ClaudeProvider, _parse_json_response


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

_VALID_ANALYSIS = {
    "note_type": "nota",
    "title": "Prueba Claude API",
    "summary": "Nota de prueba generada por ClaudeProvider.",
    "tags": ["prueba"],
    "priority": "media",
    "datetime": None,
    "reply_text": "Nota guardada correctamente.",
    "entities": [],
    "topics": ["prueba"],
}


def _make_claude_response(body: dict) -> MagicMock:
    """Crea un mock de respuesta HTTP con el cuerpo indicado."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = body
    return mock_resp


def _claude_body(text: str) -> dict:
    """Crea un body de respuesta Claude con un bloque de texto."""
    return {
        "id": "msg_01XFDUDYJgAACzvnptvVoYEL",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": text}],
        "model": "claude-3-5-sonnet-20241022",
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 100, "output_tokens": 50},
    }


def _make_provider(api_key: str = "sk-ant-test") -> ClaudeProvider:
    return ClaudeProvider(
        api_key=api_key,
        base_url="https://api.anthropic.com/v1",
        chat_model="claude-3-5-sonnet-20241022",
        timeout_seconds=5,
        http_max_retries=2,
        http_retry_delay_seconds=0,
        max_tokens=512,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tests de _parse_json_response (función auxiliar)
# ─────────────────────────────────────────────────────────────────────────────

class ParseJsonResponseTests(unittest.TestCase):

    def test_json_directo(self):
        """Parsea JSON limpio sin texto adicional."""
        text = json.dumps(_VALID_ANALYSIS)
        result = _parse_json_response(text)
        self.assertEqual(result["note_type"], "nota")

    def test_json_embebido_con_texto_antes(self):
        """Extrae JSON cuando hay texto antes del bloque {}."""
        texto_antes = "Aquí está el análisis solicitado:\n"
        text = texto_antes + json.dumps(_VALID_ANALYSIS)
        result = _parse_json_response(text)
        self.assertEqual(result["title"], "Prueba Claude API")

    def test_json_embebido_con_texto_despues(self):
        """Extrae JSON cuando hay texto después del bloque {}."""
        text = json.dumps(_VALID_ANALYSIS) + "\n\nEspero que sea útil."
        result = _parse_json_response(text)
        self.assertEqual(result["note_type"], "nota")

    def test_json_embebido_entre_texto(self):
        """Extrae JSON cuando está rodeado de texto."""
        text = "Aquí el JSON:\n" + json.dumps({"note_type": "idea", "title": "X"}) + "\nFin."
        result = _parse_json_response(text)
        self.assertEqual(result["title"], "X")

    def test_sin_json_lanza_value_error(self):
        """Lanza ValueError si no hay JSON en el texto."""
        with self.assertRaises(ValueError):
            _parse_json_response("Esto no es JSON para nada.")

    def test_json_malformado_sin_fallback_valido(self):
        """Lanza ValueError si el texto tiene {} pero no es JSON válido."""
        with self.assertRaises((ValueError, json.JSONDecodeError)):
            _parse_json_response("{ clave_sin_comillas: valor }")


# ─────────────────────────────────────────────────────────────────────────────
# Tests de ClaudeProvider.analyze_message
# ─────────────────────────────────────────────────────────────────────────────

class ClaudeProviderAnalyzeMessageTests(unittest.TestCase):

    @patch("academiaserver.ai.claude_provider.requests.post")
    def test_respuesta_correcta(self, mock_post):
        """analyze_message() retorna el dict correcto para una respuesta normal."""
        mock_post.return_value = _make_claude_response(
            _claude_body(json.dumps(_VALID_ANALYSIS))
        )
        provider = _make_provider()
        result = provider.analyze_message("prueba beta Mitzlia")
        self.assertEqual(result["note_type"], "nota")
        self.assertEqual(result["title"], "Prueba Claude API")

    @patch("academiaserver.ai.claude_provider.requests.post")
    def test_headers_correctos(self, mock_post):
        """Verifica que el request incluye x-api-key y anthropic-version."""
        mock_post.return_value = _make_claude_response(
            _claude_body(json.dumps(_VALID_ANALYSIS))
        )
        provider = _make_provider()
        provider.analyze_message("hola")
        _, kwargs = mock_post.call_args
        headers = kwargs.get("headers", {})
        self.assertIn("x-api-key", headers)
        self.assertEqual(headers["x-api-key"], "sk-ant-test")
        self.assertIn("anthropic-version", headers)
        self.assertEqual(headers["anthropic-version"], ClaudeProvider.ANTHROPIC_VERSION)

    @patch("academiaserver.ai.claude_provider.requests.post")
    def test_system_prompt_en_payload_separado(self, mock_post):
        """El system prompt va en payload['system'], no dentro de messages."""
        mock_post.return_value = _make_claude_response(
            _claude_body(json.dumps(_VALID_ANALYSIS))
        )
        provider = _make_provider()
        provider.analyze_message("hola")
        _, kwargs = mock_post.call_args
        payload = kwargs.get("json", {})
        self.assertIn("system", payload)
        # messages solo tiene un mensaje de usuario
        self.assertEqual(len(payload["messages"]), 1)
        self.assertEqual(payload["messages"][0]["role"], "user")
        # No debe haber role:system dentro de messages
        roles_en_messages = [m["role"] for m in payload["messages"]]
        self.assertNotIn("system", roles_en_messages)

    @patch("academiaserver.ai.claude_provider.requests.post")
    def test_max_tokens_en_payload(self, mock_post):
        """El payload incluye max_tokens (obligatorio en Claude API)."""
        mock_post.return_value = _make_claude_response(
            _claude_body(json.dumps(_VALID_ANALYSIS))
        )
        provider = _make_provider()
        provider.analyze_message("hola")
        _, kwargs = mock_post.call_args
        payload = kwargs.get("json", {})
        self.assertIn("max_tokens", payload)
        self.assertEqual(payload["max_tokens"], 512)

    @patch("academiaserver.ai.claude_provider.requests.post")
    def test_endpoint_correcto(self, mock_post):
        """El request se hace a /v1/messages, no a /chat/completions."""
        mock_post.return_value = _make_claude_response(
            _claude_body(json.dumps(_VALID_ANALYSIS))
        )
        provider = _make_provider()
        provider.analyze_message("hola")
        args, _ = mock_post.call_args
        url = args[0]
        self.assertIn("/messages", url)
        self.assertNotIn("chat/completions", url)

    def test_api_key_vacia_lanza_runtime_error(self):
        """RuntimeError si ANTHROPIC_API_KEY está vacía."""
        provider = _make_provider(api_key="")
        with self.assertRaises(RuntimeError) as ctx:
            provider.analyze_message("hola")
        self.assertIn("ANTHROPIC_API_KEY", str(ctx.exception))

    @patch("academiaserver.ai.claude_provider.requests.post")
    def test_sin_content_blocks_lanza_value_error(self, mock_post):
        """ValueError si la respuesta de Claude no tiene bloques de contenido."""
        mock_post.return_value = _make_claude_response(
            {"id": "msg_x", "content": [], "role": "assistant"}
        )
        provider = _make_provider()
        with self.assertRaises(ValueError) as ctx:
            provider.analyze_message("hola")
        self.assertIn("sin bloques", str(ctx.exception))

    @patch("academiaserver.ai.claude_provider.requests.post")
    def test_texto_vacio_lanza_value_error(self, mock_post):
        """ValueError si el bloque de texto está vacío."""
        mock_post.return_value = _make_claude_response(
            _claude_body("")
        )
        provider = _make_provider()
        with self.assertRaises(ValueError) as ctx:
            provider.analyze_message("hola")
        self.assertIn("vacío", str(ctx.exception))

    @patch("academiaserver.ai.claude_provider.requests.post")
    def test_json_embebido_en_texto(self, mock_post):
        """Extrae JSON aunque Claude ponga texto introductorio antes del bloque."""
        texto_con_intro = "Aquí está mi análisis:\n" + json.dumps(_VALID_ANALYSIS)
        mock_post.return_value = _make_claude_response(_claude_body(texto_con_intro))
        provider = _make_provider()
        result = provider.analyze_message("hola")
        self.assertEqual(result["note_type"], "nota")

    @patch("academiaserver.ai.claude_provider.time.sleep")
    @patch("academiaserver.ai.claude_provider.requests.post")
    def test_reintenta_en_fallo_y_recupera(self, mock_post, mock_sleep):
        """Reintenta en caso de RequestException y recupera en segundo intento."""
        error_resp = requests.exceptions.ConnectionError("timeout")
        ok_resp = _make_claude_response(_claude_body(json.dumps(_VALID_ANALYSIS)))
        mock_post.side_effect = [error_resp, ok_resp]

        provider = _make_provider()
        result = provider.analyze_message("hola")
        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(result["note_type"], "nota")

    @patch("academiaserver.ai.claude_provider.time.sleep")
    @patch("academiaserver.ai.claude_provider.requests.post")
    def test_lanza_excepcion_si_todos_los_intentos_fallan(self, mock_post, mock_sleep):
        """Propaga la excepción si todos los reintentos HTTP fallan."""
        mock_post.side_effect = requests.exceptions.ConnectionError("error")
        provider = _make_provider()
        with self.assertRaises(requests.exceptions.ConnectionError):
            provider.analyze_message("hola")
        # http_max_retries=2 → debe haberse intentado 2 veces
        self.assertEqual(mock_post.call_count, 2)

    @patch("academiaserver.ai.claude_provider.requests.post")
    def test_system_prompt_override(self, mock_post):
        """system_prompt_override reemplaza el system prompt por defecto."""
        mock_post.return_value = _make_claude_response(
            _claude_body(json.dumps(_VALID_ANALYSIS))
        )
        provider = _make_provider()
        custom_prompt = "Eres un asistente de prueba."
        provider.analyze_message("hola", system_prompt_override=custom_prompt)
        _, kwargs = mock_post.call_args
        payload = kwargs.get("json", {})
        self.assertEqual(payload["system"], custom_prompt)

    @patch("academiaserver.ai.claude_provider.requests.post")
    def test_context_incluido_en_user_message(self, mock_post):
        """El contexto se incluye en el contenido del mensaje de usuario."""
        mock_post.return_value = _make_claude_response(
            _claude_body(json.dumps(_VALID_ANALYSIS))
        )
        provider = _make_provider()
        provider.analyze_message("hola", context=["turno anterior"])
        _, kwargs = mock_post.call_args
        payload = kwargs.get("json", {})
        user_content = payload["messages"][0]["content"]
        self.assertIn("turno anterior", user_content)


# ─────────────────────────────────────────────────────────────────────────────
# Tests de configuración / inicialización
# ─────────────────────────────────────────────────────────────────────────────

class ClaudeProviderInicializacionTests(unittest.TestCase):

    def test_base_url_strip_slash(self):
        """Elimina la barra final de base_url."""
        provider = ClaudeProvider(
            api_key="key",
            base_url="https://api.anthropic.com/v1/",
            chat_model="claude-3-5-sonnet-20241022",
        )
        self.assertFalse(provider.base_url.endswith("/"))

    def test_http_max_retries_minimo_uno(self):
        """http_max_retries nunca es menor que 1."""
        provider = ClaudeProvider("key", "url", "model", http_max_retries=0)
        self.assertEqual(provider.http_max_retries, 1)

    def test_http_retry_delay_minimo_cero(self):
        """http_retry_delay_seconds nunca es negativo."""
        provider = ClaudeProvider("key", "url", "model", http_retry_delay_seconds=-5)
        self.assertEqual(provider.http_retry_delay_seconds, 0)

    def test_max_tokens_default(self):
        """max_tokens por defecto es 1024."""
        provider = ClaudeProvider("key", "url", "model")
        self.assertEqual(provider.max_tokens, 1024)


if __name__ == "__main__":
    unittest.main()
