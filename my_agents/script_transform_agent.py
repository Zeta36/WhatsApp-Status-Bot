import logging
import os
from agents import Agent, Runner, ModelSettings

log = logging.getLogger(__name__)

def run(script: str, instruction: str, model: str = None) -> str:
    """
    Agente que transforma un guion recibido según una instrucción personalizada.
    Devuelve el texto transformado.
    """
    log.info("[ScriptTransformAgent] Iniciando agente de transformación...")
    if not model:
        model = os.getenv("SCRIPT_TRANSFORM_MODEL")
    agent = Agent(
        name="ScriptTransformAgent",
        model=model,
        instructions=(
            "Eres un experto transformador de textos literarios y divulgativos. "
            "Sigue al pie de la letra la instrucción dada por el usuario. "
            "Devuelve únicamente el texto transformado, sin explicaciones ni comentarios."
        ),
        model_settings=ModelSettings(temperature=1.0),
    )
    prompt = f"{instruction}\n\nTexto original:\n{script}\n\nTexto transformado:"
    # Ejecuta de forma sincrónica usando el patrón correcto del SDK
    result = Runner.run_sync(agent, prompt)
    log.info("[ScriptTransformAgent] Guion transformado con instrucción: %s", instruction)
    return result.final_output.strip()
