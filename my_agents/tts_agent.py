import logging
import openai
from pathlib import Path
import os

def run(text: str, voice: str, model: str, out_path: Path) -> str:
    """Genera audio MP3 con la voz/tono configurados."""
    logging.info("[TTS] Sintetizando voz (%s)…", voice)
    tts_instructions = os.getenv("TTS_TONE")
    with openai.audio.speech.with_streaming_response.create(
        model=model,
        voice=voice,
        input=text,
        instructions=tts_instructions,
    ) as response:
        response.stream_to_file(str(out_path))
    logging.info("[TTS] Audio en %s", out_path)

    return str(out_path)
