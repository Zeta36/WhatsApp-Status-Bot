import base64
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, List

import openai
import requests  # para descargar URLs si no recibimos base64
from openai import OpenAIError

log     = logging.getLogger(__name__)

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

def _edit(prompt: str, size: str, quality: str, prev_path: str) -> Any:
    with open(prev_path, "rb") as img_f:
        rsp = openai.images.edit(
            model="gpt-image-1",
            image=img_f,      # UN solo archivo para coherencia
            prompt=prompt,
            n=1,
            size=size,
            quality=quality,
            moderation="low"
        )
    return rsp.data[0]

def _split_summary(summary: str, parts: int = 3) -> List[str]:
    words = summary.split()
    size = max(1, len(words) // parts)
    captions: List[str] = []
    for i in range(parts):
        start = i * size
        end = (i + 1) * size if i < parts - 1 else len(words)
        captions.append(" ".join(words[start:end]))
    return captions

def run(summary: str, how_many: int, out_dir: str) -> List[str]:
    """
    Split summary into `how_many` parts and generate images accordingly:
     - idx=0 → generate with first caption
     - subsequent images preserve initial style
    """
    captions = _split_summary(summary, parts=how_many)
    # Load general image style
    style = os.getenv("IMAGE_STYLE", "")
    # Load image quality from env
    quality = os.getenv("IMAGE_QUALITY", "medium")
    out_paths: List[str] = []
    out_path_dir = Path(out_dir)
    out_path_dir.mkdir(exist_ok=True)

    for idx, caption in enumerate(captions):
         
        for attempt in range(1, MAX_RETRY+1):
            try:
                # Llama a la API usando siempre generación, preservando estilo en partes posteriores
                if idx == 0:
                    prompt = f"Estilo general: {style}. Ilustración inicial sobre: {caption}"
                else:
                    prompt = f"Estilo general: {style}. Ilustración sobre: {caption}, conservando el estilo de la primera imagen"
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
