from academiaserver.ai.privacy import is_sensitive_message
from academiaserver.ai.provider import AIProvider


class HybridProvider(AIProvider):
    def __init__(
        self,
        local_provider: AIProvider,
        cloud_provider: AIProvider | None,
        allow_cloud_fallback: bool,
        allow_sensitive_to_cloud: bool,
    ):
        self.local_provider = local_provider
        self.cloud_provider = cloud_provider
        self.allow_cloud_fallback = allow_cloud_fallback
        self.allow_sensitive_to_cloud = allow_sensitive_to_cloud

    def analyze_message(self, text: str, context: list[str] = [], memory: list[dict] = []) -> dict:
        try:
            return self.local_provider.analyze_message(text, context=context, memory=memory)
        except Exception as local_error:
            if not self.allow_cloud_fallback:
                raise RuntimeError(f"Local fallo y fallback cloud desactivado: {local_error}")

            if self.cloud_provider is None:
                raise RuntimeError(
                    f"Local fallo y no hay proveedor cloud configurado: {local_error}"
                )

            if (not self.allow_sensitive_to_cloud) and is_sensitive_message(text):
                raise RuntimeError(
                    "Mensaje sensible detectado; no se permite enviar a proveedor cloud"
                )

            return self.cloud_provider.analyze_message(text, context=context, memory=memory)
