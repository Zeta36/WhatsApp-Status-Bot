import logging
from agents import Agent, WebSearchTool, Runner, ModelSettings

log = logging.getLogger(__name__)

def run(topic: str, model: str) -> str:
    """Devuelve un resumen web sobre el topic."""
    log.info("[WebSearch] Buscando info sobre: %s", topic)

    agent = Agent(
        name="WebResearcher",
        model=model,
        instructions="Eres un agente especializado en dar ideas (varias siempre) para generar un profundo texto a partir del tema y la información encontrada.",
        tools=[WebSearchTool()],
        model_settings=ModelSettings(temperature=1.0),
    )
    result = Runner.run_sync(agent, f"Ideas para crear un texto sobre {topic}")
    return result.final_output.strip()
