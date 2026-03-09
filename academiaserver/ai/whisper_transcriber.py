"""
Transcriptor de audio con patrón local → cloud fallback.

Intenta transcribir con faster-whisper (local/GPU) primero.
Si falla (import error, ffmpeg ausente, etc.), usa OpenAI Whisper API.
Si ambos fallan, retorna None (degradación suave).
"""

import logging
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# Singleton del modelo faster-whisper (se carga al primer uso)
_whisper_model = None


def _get_model(model_name: str, device: str, compute_type: str):
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel

        logger.info(
            "Cargando modelo faster-whisper '%s' en %s (%s)...",
            model_name,
            device,
            compute_type,
        )
        _whisper_model = WhisperModel(model_name, device=device, compute_type=compute_type)
        logger.info("Modelo faster-whisper cargado.")
    return _whisper_model


class WhisperTranscriber:
    """Transcriptor híbrido: faster-whisper local → OpenAI API como fallback."""

    def __init__(
        self,
        model_name: str = "small",
        language: str = "es",
        device: str = "cpu",
        compute_type: str = "int8",
        openai_api_key: str = "",
        openai_base_url: str = "https://api.openai.com/v1",
        timeout_seconds: int = 60,
    ):
        self.model_name = model_name
        self.language = language
        self.device = device
        self.compute_type = compute_type
        self.openai_api_key = openai_api_key
        self.openai_base_url = openai_base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def transcribe(self, audio_path: Path) -> str | None:
        """
        Transcribe el archivo de audio en audio_path.

        Retorna el texto transcrito, o None si ambos métodos fallan.
        """
        try:
            text = self._transcribe_local(audio_path)
            logger.info("Transcripción local OK (%d chars).", len(text))
            return text
        except Exception as exc:
            logger.warning("Transcripción local falló: %s. Intentando OpenAI...", exc)

        try:
            text = self._transcribe_openai(audio_path)
            logger.info("Transcripción OpenAI OK (%d chars).", len(text))
            return text
        except Exception as exc:
            logger.error("Transcripción OpenAI también falló: %s.", exc)

        return None

    def _transcribe_local(self, audio_path: Path) -> str:
        model = _get_model(self.model_name, self.device, self.compute_type)
        segments, _ = model.transcribe(
            str(audio_path),
            language=self.language,
            beam_size=5,
        )
        return " ".join(seg.text.strip() for seg in segments).strip()

    def _transcribe_openai(self, audio_path: Path) -> str:
        if not self.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY no configurada; no se puede usar el fallback cloud.")

        url = f"{self.openai_base_url}/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self.openai_api_key}"}

        with audio_path.open("rb") as f:
            files = {"file": (audio_path.name, f, "audio/ogg")}
            data = {"model": "whisper-1", "language": self.language}
            response = requests.post(
                url,
                headers=headers,
                files=files,
                data=data,
                timeout=self.timeout_seconds,
            )

        response.raise_for_status()
        return response.json().get("text", "").strip()
