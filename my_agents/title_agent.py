import logging
import os
from agents import Agent, Runner, ModelSettings

log = logging.getLogger(__name__)

def run(script: str, model: str) -> str:
    """
    Agente que genera un título descriptivo breve para el guion del video.
    """
    log.info("[TitleAgent] Generando título descriptivo...")
    agent = Agent(
        name="TitleGenerator",
        model=model,
        instructions=(
            "Eres un asistente que genera un título breve y descriptivo "
            "a partir de un guion de video. "
            "Devuelve únicamente el título, sin comillas ni signos de puntuación. "
            "El título debe ser descriptivo y conciso. "
            "Solo la primera letra va en mayúsculas. "
            "IMPORTANTE: El idioma del título generado debe coincidir con el usado en el guion. "
            "Si el guion está en inglés, el título debe ser en inglés. "
            "Si el guion está en español, el título debe ser en español. Etc."
            "Ejemplo entrada: 'In the theatre of quantum possibility, a photon pirouettes between paths unseen until the act of scrutiny summons its defining choice. Every gaze disturbs the script, transforms a probabilistic ballet into a singular story. We chase certainty through the veils of uncertainty'"
            "Ejemplo salida: 'In the theatre of quantum possibility'"
            
        ),
        tools=[],
    )
    result = Runner.run_sync(agent, script)
    title = result.final_output.strip()    
    return title
