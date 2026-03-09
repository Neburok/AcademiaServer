"""
Tests para WhisperTranscriber.

Cobertura:
- Transcripción local exitosa (mock de faster-whisper)
- Fallback a OpenAI cuando el local falla
- Retorno None cuando ambos métodos fallan
- Verificación del POST multipart a OpenAI
- Integración con el bot: voz → _process_text llamado
"""

import io
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from academiaserver.ai.whisper_transcriber import WhisperTranscriber


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_whisper_singleton():
    """Resetea el singleton del modelo faster-whisper entre tests."""
    import academiaserver.ai.whisper_transcriber as mod
    original = mod._whisper_model
    mod._whisper_model = None
    yield
    mod._whisper_model = original


@pytest.fixture
def audio_file(tmp_path) -> Path:
    """Crea un archivo de audio ficticio para los tests."""
    p = tmp_path / "nota.ogg"
    p.write_bytes(b"fake ogg audio data")
    return p


@pytest.fixture
def transcriber() -> WhisperTranscriber:
    return WhisperTranscriber(
        model_name="small",
        language="es",
        device="cpu",
        compute_type="int8",
        openai_api_key="sk-test-key",
        openai_base_url="https://api.openai.com/v1",
        timeout_seconds=10,
    )


# ---------------------------------------------------------------------------
# test_transcribe_local_ok
# ---------------------------------------------------------------------------

def test_transcribe_local_ok(transcriber, audio_file):
    """faster-whisper disponible → retorna texto transcrito."""
    mock_segment = MagicMock()
    mock_segment.text = "Hola Profesor"

    mock_model = MagicMock()
    mock_model.transcribe.return_value = ([mock_segment], MagicMock())

    with patch(
        "academiaserver.ai.whisper_transcriber._get_model",
        return_value=mock_model,
    ):
        result = transcriber.transcribe(audio_file)

    assert result == "Hola Profesor"
    mock_model.transcribe.assert_called_once_with(
        str(audio_file), language="es", beam_size=5
    )


# ---------------------------------------------------------------------------
# test_local_falla_fallback_openai
# ---------------------------------------------------------------------------

def test_local_falla_fallback_openai(transcriber, audio_file):
    """Si el local lanza excepción → cae a OpenAI y retorna texto."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"text": "Texto desde OpenAI"}
    mock_response.raise_for_status.return_value = None

    with (
        patch(
            "academiaserver.ai.whisper_transcriber._get_model",
            side_effect=ImportError("faster-whisper no instalado"),
        ),
        patch("requests.post", return_value=mock_response) as mock_post,
    ):
        result = transcriber.transcribe(audio_file)

    assert result == "Texto desde OpenAI"
    mock_post.assert_called_once()


# ---------------------------------------------------------------------------
# test_ambos_fallan_retorna_none
# ---------------------------------------------------------------------------

def test_ambos_fallan_retorna_none(transcriber, audio_file):
    """Si local y OpenAI fallan → retorna None (degradación suave)."""
    with (
        patch(
            "academiaserver.ai.whisper_transcriber._get_model",
            side_effect=RuntimeError("error local"),
        ),
        patch("requests.post", side_effect=ConnectionError("sin red")),
    ):
        result = transcriber.transcribe(audio_file)

    assert result is None


# ---------------------------------------------------------------------------
# test_openai_multipart
# ---------------------------------------------------------------------------

def test_openai_multipart(transcriber, audio_file):
    """Verifica que el POST a OpenAI usa el endpoint y parámetros correctos."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"text": "multipart ok"}
    mock_response.raise_for_status.return_value = None

    with (
        patch(
            "academiaserver.ai.whisper_transcriber._get_model",
            side_effect=RuntimeError("local no disponible"),
        ),
        patch("requests.post", return_value=mock_response) as mock_post,
    ):
        result = transcriber._transcribe_openai(audio_file)

    assert result == "multipart ok"
    call_kwargs = mock_post.call_args
    assert call_kwargs[0][0] == "https://api.openai.com/v1/audio/transcriptions"
    assert call_kwargs[1]["headers"] == {"Authorization": "Bearer sk-test-key"}
    assert call_kwargs[1]["data"] == {"model": "whisper-1", "language": "es"}
    assert "file" in call_kwargs[1]["files"]


# ---------------------------------------------------------------------------
# test_openai_sin_api_key_lanza_error
# ---------------------------------------------------------------------------

def test_openai_sin_api_key_lanza_error(audio_file):
    """Sin API key, _transcribe_openai debe lanzar RuntimeError."""
    transcriber_sin_key = WhisperTranscriber(openai_api_key="")

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        transcriber_sin_key._transcribe_openai(audio_file)


# ---------------------------------------------------------------------------
# test_roundtrip_bot
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_roundtrip_bot(tmp_path):
    """
    Simula el flujo completo: handler de voz → transcripción → _process_text.

    Verifica que handle_voice_message descarga el audio, llama a transcribe()
    y pasa el texto a _process_text.
    """
    from academiaserver.clients.telegram_bot import handle_voice_message

    # Archivo de audio temporal
    audio_path = tmp_path / "voz.ogg"
    audio_path.write_bytes(b"fake audio")

    # Mock de update con mensaje de voz
    mock_voice = MagicMock()
    mock_file = AsyncMock()
    mock_file.download_to_drive = AsyncMock()
    mock_voice.get_file = AsyncMock(return_value=mock_file)

    mock_message = MagicMock()
    mock_message.chat_id = 12345
    mock_message.voice = mock_voice
    mock_message.reply_text = AsyncMock()

    mock_update = MagicMock()
    mock_update.message = mock_message

    mock_context = MagicMock()
    mock_context.application.bot_data = {}

    with (
        patch(
            "academiaserver.clients.telegram_bot.CHAT_ID_ENV",
            "12345",
        ),
        patch(
            "academiaserver.clients.telegram_bot._whisper"
        ) as mock_whisper,
        patch(
            "academiaserver.clients.telegram_bot._process_text",
            new_callable=AsyncMock,
        ) as mock_process,
        patch("tempfile.NamedTemporaryFile") as mock_tmp,
    ):
        # Configurar el archivo temporal
        mock_tmp_file = MagicMock()
        mock_tmp_file.name = str(audio_path)
        mock_tmp.__enter__ = MagicMock(return_value=mock_tmp_file)
        mock_tmp.__exit__ = MagicMock(return_value=False)
        mock_tmp.return_value.__enter__ = MagicMock(return_value=mock_tmp_file)
        mock_tmp.return_value.__exit__ = MagicMock(return_value=False)

        mock_whisper.transcribe.return_value = "Nota de voz transcrita"

        await handle_voice_message(mock_update, mock_context)

    mock_process.assert_called_once_with(
        mock_update, "Nota de voz transcrita", mock_context
    )
