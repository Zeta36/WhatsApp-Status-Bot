import logging
from agents import Agent, Runner
import json

log = logging.getLogger(__name__)

def run(final_script: str, model: str) -> tuple[str, bool]:
    """
    Agente que detecta si el texto está en español. Si no lo está, genera la mejor traducción posible al español.
    Devuelve el texto en español (o el original si ya estaba en español).
    """
    log.info("[LangCheckAgent] Detectando idioma y traduciendo si es necesario...")
    
    agent = Agent(
        name="LangCheckAgent",
        model=model,
        instructions=(
            "Eres un experto lingüista y traductor profesional especializado en detección de idiomas y traducción al español. "
            "Analiza el texto dado y determina si está en español o en otro idioma. "
            "Responde SOLO en formato JSON con esta estructura exacta:\n"
            "```\n"
            "{\n"
            "  \"is_spanish\": true|false,  // true si el texto original está en español, false en caso contrario\n"
            "  \"translation\": \"texto traducido al español\" // Si is_spanish es false, incluye la traducción completa. Si is_spanish es true, devuelve el texto original sin cambios.\n"
            "}\n"
            "```\n"
            "Reglas importantes:\n"
            "1. El JSON debe ser válido (comillas dobles, sin comas extra al final)\n"
            "2. Si el texto ya está en español, marca is_spanish como true y devuelve el texto original exacto en translation\n"
            "3. Si encuentras un texto en otro idioma, marca is_spanish como false y proporciona una traducción adecuada en translation\n"
            "4. SOLO responde con el JSON, nada más\n"
        ),
        tools=[],
    )
    
    result = Runner.run_sync(agent, final_script)
    output = result.final_output.strip()
    
    try:
        # Analizar el JSON de respuesta
        response_data = json.loads(output)
        is_spanish = response_data.get('is_spanish', False)
        translation = response_data.get('translation', final_script)
        
        if is_spanish:
            log.info("[LangCheckAgent] El modelo detectó que el texto ya está en español")
            return final_script, False
        else:
            log.info("[LangCheckAgent] El modelo detectó que el texto no está en español, usando traducción")
            return translation, True
            
    except json.JSONDecodeError as e:
        log.warning(f"[LangCheckAgent] Error al analizar JSON: {e}. Respuesta recibida: {output}")
        log.warning("[LangCheckAgent] Fallback: Asumiendo que no se requiere traducción")
        return final_script, False
