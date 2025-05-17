import base64
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, List

import openai
import requests  # para descargar URLs si no recibimos base64
from agents import Agent, Runner, ModelSettings
from openai import OpenAIError

log = logging.getLogger(__name__)

# Carpeta staging (se moverán luego a runs/)
MEDIA_DIR = Path(__file__).parent.parent / "media"
MEDIA_DIR.mkdir(exist_ok=True)

MAX_RETRY = 3
BACKOFF   = 0.8

def _save_image(data: bytes, out_dir: Path) -> str:
    fn   = f"img_{int(time.time())}_{uuid.uuid4().hex}.png"
    path = out_dir / fn
    with open(path, "wb") as f:
        f.write(data)
    return str(path)

def _generate(prompt: str, size: str, quality: str) -> Any:
    rsp = openai.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        n=1,
        size=size,
        quality=quality,
        moderation="low"
    )
    return rsp.data[0]

def _prepare_prompt(caption: str, style: str, script_context: str, idx: int, total: int) -> str:
    model = os.getenv("SCRIPT_MODEL", "gpt-4o")
    instructions = (
        "Eres un agente que genera prompts detallados para imágenes con gpt-image-1. "
        "Recibirá en la entrada el siguiente texto y deberá responder solo con el prompt para gpt-image-1."
    )
    agent = Agent(
        name="ImagePromptGenerator",
        model=model,
        instructions=instructions,
        tools=[],        
    )
    input_text = (
        f"Escena {idx+1}/{total}: {caption}\n"
        f"Estilo: {style}\n"
        f"Contexto del guión:\n{script_context}"
    )
    result = Runner.run_sync(agent, input_text)
    return result.final_output.strip()

def _split_summary(summary: str, parts: int = 3) -> List[str]:
    words = summary.split()
    size = max(1, len(words) // parts)
    captions: List[str] = []
    for i in range(parts):
        start = i * size
        end = (i + 1) * size if i < parts - 1 else len(words)
        captions.append(" ".join(words[start:end]))
    return captions

def run(summary: str, how_many: int, out_dir: str, full_script: str = None) -> List[str]:
    """
    Split summary into `how_many` parts and generate images accordingly, but now also provide the full script for context:
     - idx=0 → generate with first caption
     - subsequent images preserve initial style
     - full_script: if provided, is included in the prompt for more context
    """
    captions = _split_summary(summary, parts=how_many)
    # Load general image style
    style = os.getenv("IMAGE_STYLE", "")
    # Load image quality from env
    quality = os.getenv("IMAGE_QUALITY", "medium")
    out_paths: List[str] = []
    out_path_dir = Path(out_dir)
    out_path_dir.mkdir(exist_ok=True)

    # Usa el guion completo si está disponible, si no, usa el summary como fallback
    script_context = full_script if full_script else summary

    for idx, caption in enumerate(captions):
        for attempt in range(1, MAX_RETRY+1):
            try:
                # Generar prompt con el Agent y crear imagen
                prompt = _prepare_prompt(caption, style, script_context, idx, how_many)
                log.info("[ImageAgent] Prompt escena %d/%d: %s", idx+1, how_many, prompt)
                item = _generate(prompt, size="1024x1024", quality=quality)

                # saca bytes de la respuesta
                if hasattr(item, "b64_json") and item.b64_json:
                    data = base64.b64decode(item.b64_json)
                elif hasattr(item, "url") and item.url:
                    r = requests.get(item.url)
                    r.raise_for_status()
                    data = r.content
                else:
                    raise ValueError("Ni b64_json ni URL en la respuesta.")

                # guarda el PNG
                path = Path(MEDIA_DIR) / Path(_save_image(data, MEDIA_DIR)).name
                out_paths.append(str(path))
                log.info("[ImageAgent] guardada %s", path)
                break

            except (OpenAIError, ValueError, requests.HTTPError) as e:
                log.warning("[ImageAgent] %s intento %d/%d", 
                            e.__class__.__name__, attempt, MAX_RETRY)
                if attempt == MAX_RETRY:
                    raise
                time.sleep(BACKOFF * attempt)

    # Mueve las imágenes de media/ a out_dir final
    final_paths: List[str] = []
    for p in out_paths:
        dst = os.path.join(out_dir, os.path.basename(p))
        os.replace(p, dst)
        final_paths.append(dst)

    return final_paths
