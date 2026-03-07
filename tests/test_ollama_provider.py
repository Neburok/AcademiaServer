import json
import unittest
from unittest.mock import Mock, patch

import requests

from academiaserver.ai.ollama_provider import OllamaProvider


class OllamaProviderTests(unittest.TestCase):
    @patch("academiaserver.ai.ollama_provider.requests.post")
    def test_ollama_provider_reintenta_y_recupera(self, mock_post):
        fail = requests.ConnectionError("sin conexion")
        ok_response = Mock()
        ok_response.raise_for_status.return_value = None
        ok_response.json.return_value = {
            "message": {
                "content": json.dumps(
                    {
                        "note_type": "nota",
                        "title": "Titulo",
                        "summary": "Resumen",
                        "tags": [],
                        "priority": "media",
                        "datetime": None,
                        "reply_text": "OK",
                    }
                )
            }
        }
        mock_post.side_effect = [fail, ok_response]

        provider = OllamaProvider(
            base_url="http://localhost:11434",
            chat_model="gemma3",
            timeout_seconds=5,
            http_max_retries=2,
            http_retry_delay_seconds=0,
        )

        result = provider.analyze_message("mensaje de prueba")
        self.assertEqual(result["title"], "Titulo")
        self.assertEqual(mock_post.call_count, 2)

    @patch("academiaserver.ai.ollama_provider.requests.post")
    def test_ollama_provider_falla_si_agota_reintentos(self, mock_post):
        mock_post.side_effect = requests.Timeout("timeout")
        provider = OllamaProvider(
            base_url="http://localhost:11434",
            chat_model="gemma3",
            timeout_seconds=1,
            http_max_retries=2,
            http_retry_delay_seconds=0,
        )

        with self.assertRaises(requests.RequestException):
            provider.analyze_message("mensaje")


if __name__ == "__main__":
    unittest.main()
