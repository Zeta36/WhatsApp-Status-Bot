# agents/script_agent.py

import logging
import os
from agents import Agent, Runner, ModelSettings

log = logging.getLogger(__name__)

"""Delay env var reading; load VIDEO_TEXT_LEN and SCRIPT_TOPIC inside run()."""
import os  # ensure os is imported

def run(summary: str, model: str) -> str:
    """
    Agente que convierte un resumen en una cita/aforismo breve.
    Devuelve el texto generado.
    """
    log.info("[ScriptAgent] Iniciando agente de guion...")
    # Load environment settings at runtime
    video_text_len_str = os.getenv("VIDEO_TEXT_LEN")
    if video_text_len_str is None:
        raise ValueError("VIDEO_TEXT_LEN must be set in environment")
    video_text_len = int(video_text_len_str)
    script_topic = os.getenv("SCRIPT_TOPIC")
    if script_topic is None:
        raise ValueError("SCRIPT_TOPIC must be set in environment")
    agent = Agent(
        name="ScriptGenerator",
        model=model,
        # Use f-strings to inject script length and topic
        instructions=(
            f"Eres un agente creativo que, a partir de un conjunto de ideas, "
            f"genera una cita o aforismo profundo. "
            f"Responde únicamente con la cita generada. "
            f"El tema sobre el que escribir es: {script_topic}. "
            f"IMPORTANTE: la cita debe tener {video_text_len} palabras, ni más corta ni más larga."
        ),
        tools=[],  # no necesita herramientas externas
        model_settings=ModelSettings(temperature=1.0),
    )
    # Ejecuta de forma sincrónica
    result = Runner.run_sync(agent, summary)
    quote = result.final_output.strip()
    log.info("[ScriptAgent] Cita generada: %s", quote)
    return quote
