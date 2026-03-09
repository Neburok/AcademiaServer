import unittest

from academiaserver.ai.hybrid_provider import HybridProvider


class ProviderOk:
    def analyze_message(
        self, _text: str, context: list = [], memory: list = [], system_prompt_override=None
    ) -> dict:
        return {"note_type": "nota", "title": "ok"}


class ProviderFail:
    def analyze_message(
        self, _text: str, context: list = [], memory: list = [], system_prompt_override=None
    ) -> dict:
        raise RuntimeError("fallo")


class HybridProviderTests(unittest.TestCase):
    def test_hybrid_usa_local_si_funciona(self):
        provider = HybridProvider(
            local_provider=ProviderOk(),
            cloud_provider=ProviderFail(),
            allow_cloud_fallback=True,
            allow_sensitive_to_cloud=False,
        )
        result = provider.analyze_message("mensaje")
        self.assertEqual(result["title"], "ok")

    def test_hybrid_usa_cloud_si_local_falla(self):
        provider = HybridProvider(
            local_provider=ProviderFail(),
            cloud_provider=ProviderOk(),
            allow_cloud_fallback=True,
            allow_sensitive_to_cloud=False,
        )
        result = provider.analyze_message("mensaje normal")
        self.assertEqual(result["title"], "ok")

    def test_hybrid_bloquea_cloud_en_mensaje_sensible(self):
        provider = HybridProvider(
            local_provider=ProviderFail(),
            cloud_provider=ProviderOk(),
            allow_cloud_fallback=True,
            allow_sensitive_to_cloud=False,
        )
        with self.assertRaises(RuntimeError):
            provider.analyze_message("mi password es 123456")


if __name__ == "__main__":
    unittest.main()
