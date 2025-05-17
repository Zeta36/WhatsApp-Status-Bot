#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orquesta: búsqueda → imágenes → TTS → vídeo → publicación Whatsapp.
"""

import os
import logging
import shutil

# Nota: moviepy ahora se importa en utils.video_helper

import openai
from utils.helper import bootstrap, new_run_dir
from my_agents.websearch_agent import run as web_search
from my_agents.illustration_agent import run as make_images
from my_agents.tts_agent import run as make_audio
from my_agents.script_agent import run as make_script
from my_agents.title_agent import run as make_title
from my_agents.langcheck_agent import run as translate_script
from my_agents.script_transform_agent import run as transform_script
from my_agents.web_image_agent import fetch_images_via_bing
from utils.selenium_helper import publish

import numpy as np
# Nota: PIL/textwrap ahora se importan en utils.video_helper

# === 0. Arranque =============================================================
bootstrap()
openai.api_key = os.getenv("OPENAI_API_KEY")

TOPIC      = os.getenv("WEB_SEARCH_TOPIC")
VOICE      = os.getenv("TTS_VOICE")
TTS_MODEL  = os.getenv("TTS_MODEL")
TITLE_MODEL = os.getenv("TITLE_MODEL")
IMG_MODEL  = os.getenv("IMAGE_GEN_MODEL")
TEXT_MODEL = os.getenv("WEB_SEARCH_MODEL")
CAPTION_TEXT   = os.getenv("CAPTION_TEXT")
TTS_TONE   = os.getenv("TTS_TONE")
IMAGE_COUNT = int(os.getenv("IMAGE_COUNT"))
SCRIPT_MODEL = os.getenv("SCRIPT_MODEL")
SCRIPT_TRANSFORM_MODEL = os.getenv("SCRIPT_TRANSFORM_MODEL")
KEYWORK_IMAGE_SEARCH = os.getenv("KEYWORK_IMAGE_SEARCH")
USE_SCRIPT_FILE = os.getenv("USE_SCRIPT_FILE", "false").lower() == "true"
USE_CAPTION_FILE = os.getenv("USE_CAPTION_FILE", "false").lower() == "true"

# === 1. Directorio de ejecución ==============================================
run_dir = new_run_dir()
logging.info("[Main] Carpeta de ejecución: %s", run_dir)

# Logger para mensajes de salida de agentes
out_log = logging.getLogger("AGENTS_OUT")

# Comprobamos si se va a usar un audio personalizado
USE_CUSTOM_AUDIO = os.getenv("USE_CUSTOM_AUDIO", "false").lower() == "true"
CUSTOM_AUDIO_FILE = os.getenv("CUSTOM_AUDIO_FILE", "input.mp3")

if USE_CUSTOM_AUDIO:
    # Modo de audio personalizado - omitimos toda la generación de guión y TTS
    custom_audio_path = os.path.join('media', CUSTOM_AUDIO_FILE)
    
    if not os.path.isfile(custom_audio_path):
        logging.error(f"No se encontró el archivo de audio personalizado: {custom_audio_path}")
        raise FileNotFoundError(f"No se encontró el archivo de audio personalizado: {custom_audio_path}")
    
    logging.info(f"[Main] Usando archivo de audio personalizado: {custom_audio_path}")
    
    # Copiamos el archivo de audio personalizado al directorio de ejecución
    audio_file = os.path.join(run_dir, "voice.mp3")
    shutil.copy2(custom_audio_path, audio_file)
    
    # Como no tenemos guión, usamos placeholders
    final_script = "Audio personalizado"
    translated_script = final_script
    hubo_traduccion = False
    summary = "Audio personalizado"  # resumen para imágenes si se necesita
    
    # Generar un título simple
    video_title = "Video con audio personalizado - " + os.path.splitext(os.path.basename(CUSTOM_AUDIO_FILE))[0]
    logging.info(f"[Main] Título generado: {video_title}")
    
    # No hay script real para mostrar
    script = final_script
    
    out_log.info("[Main] Usando modo de audio personalizado, omitiendo generación de guión y TTS")
    
else:
    # === 1. Flujo normal - Búsqueda Web + Procesamiento ========================
    if (os.getenv("USE_SCRIPT_FILE", "false").lower() == "true" and 
            os.path.isfile(os.path.join('media', 'script.txt'))):
        # Usar archivo de script existente
        script_file = os.path.join('media', 'script.txt')
        logging.info("[Main] Usando script.txt encontrado en carpeta media")
        with open(script_file, 'r', encoding='utf-8') as file:
            final_script = file.read().strip()
        summary = final_script[:300]  # resumen para imágenes
    else:
        # Búsqueda web automatizada
        search_results = web_search(TOPIC, TEXT_MODEL)
        out_log.info("[WebSearchAgent]\n%s\n", search_results)

        # === 2. Generación de Guión =================================================
        # Nota: La función make_script solo recibe el resumen y el modelo, el tema se toma de SCRIPT_TOPIC en .env
        script = make_script(search_results, SCRIPT_MODEL)
        logging.info("[ScriptAgent] Guión generado")    
        
        # Opcional: transformación adicional del guión
        if os.getenv("SCRIPT_TRANSFORM_ENABLED", "false").lower() == "true":
            transform_instruction = os.getenv("SCRIPT_TRANSFORM_INSTRUCTION", "")
            final_script = transform_script(script, transform_instruction, SCRIPT_TRANSFORM_MODEL)
            logging.info("[ScriptTransformAgent] Guión transformado")
        else:
            final_script = script
        
        summary = search_results[:300]  # resumen para imágenes

    # Verificar si se necesita traducir el texto
    translated_script, hubo_traduccion = translate_script(final_script, SCRIPT_MODEL)
    out_log.info("[LangCheckAgent]\n%s\nTraducción:%s\n", translated_script, hubo_traduccion)

    # Generar título para la publicación de WhatsApp
    video_title = make_title(final_script, TITLE_MODEL)
    logging.info("[TitleAgent] Título generado: %s", video_title)

    # === 4. Texto + audio ========================================================
    script = f"{final_script}"
    audio_file = make_audio(
        script, VOICE, TTS_MODEL, os.path.join(run_dir, "voice.mp3")
    )
    out_log.info("[TTS]\n%s\n", script)             # ← texto enviado a voz
    out_log.info("[Audio] %s", audio_file)

# === 3. Ilustraciones ===
image_source = os.getenv("IMAGE_SOURCE", "api")

if image_source == "web":
    # Descargar imágenes en paralelo (una por tema)
    img_files_all = []
    topic_imgs = fetch_images_via_bing(KEYWORK_IMAGE_SEARCH, count=IMAGE_COUNT, out_dir=run_dir)
    if topic_imgs:
        img_files_all.extend(topic_imgs)
    
    if img_files_all:
        img_files = img_files_all[:IMAGE_COUNT]
    else:
        # Si no hay imágenes de Bing, usar OpenAI como fallback
        logging.warning("No se encontraron imágenes con Bing, intentando con OpenAI API...")
        img_files = make_images(summary, IMAGE_COUNT, run_dir)
elif image_source == "local":
    # Usar imágenes de la carpeta media
    media_dir = os.path.join(os.path.dirname(__file__), 'media')
    if not os.path.exists(media_dir):
        os.makedirs(media_dir)
    
    # Obtener lista de archivos de imagen soportados
    img_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
    img_files = []
    
    # Buscar archivos de imagen en el directorio media
    for root, _, files in os.walk(media_dir):
        for file in sorted(files):  # Ordenar alfabéticamente
            if file.lower().endswith(img_extensions):
                img_files.append(os.path.abspath(os.path.join(root, file)))
                if len(img_files) >= IMAGE_COUNT:
                    break
        if img_files:  # Si ya encontramos suficientes imágenes, salir del bucle
            break
    
    # Mover las imágenes al directorio de ejecución
    if img_files:
        moved_files = []
        for i, img_path in enumerate(img_files[:IMAGE_COUNT]):
            try:
                # Generar un nombre de archivo único para el destino
                ext = os.path.splitext(img_path)[1]
                dest_path = os.path.join(run_dir, f'local_img_{i+1}{ext}')
                shutil.move(img_path, dest_path)
                moved_files.append(dest_path)
                logging.info(f"Imagen movida: {img_path} -> {dest_path}")
            except Exception as e:
                logging.error(f"Error moviendo imagen {img_path}: {e}")
        
        if not moved_files:
            logging.error("No se pudieron mover las imágenes locales. Usando imágenes por defecto.")
            img_files = make_images(summary, IMAGE_COUNT, run_dir)
        else:
            img_files = moved_files
    else:
        logging.warning("No se encontraron imágenes en la carpeta 'media'. Usando generación de imágenes por defecto.")
        img_files = make_images(summary, IMAGE_COUNT, run_dir)
else:
    # Genera N imágenes con la API de OpenAI (comportamiento por defecto)
    img_files = make_images(summary, IMAGE_COUNT, run_dir)
out_log.info("[Illustration]\n%s\n", "\n".join(img_files))

# === 4. Vídeo y audio ========================================================

# === 5. Vídeo ================================================================
from utils.video_helper import generate_video

# Verificar si existe caption.txt en la carpeta media
caption_file_path = os.path.join('media', 'caption.txt')
if USE_CAPTION_FILE and os.path.isfile(caption_file_path):
    logging.info("[Main] Utilizando caption.txt encontrado en carpeta media")
    with open(caption_file_path, 'r', encoding='utf-8') as file:
        caption_text = file.read().strip()
else:
    caption_text = CAPTION_TEXT
    
# Generar vídeo con las imágenes, audio y subtítulos
subtitle_font_size = int(os.getenv("SUBTITLE_FONT_SIZE", "30"))
video_path = generate_video(
    audio_file=audio_file,
    img_files=img_files,
    script=script,
    translated_script=translated_script,
    hubo_traduccion=hubo_traduccion,
    caption_text=caption_text,
    run_dir=run_dir,
    font_size=subtitle_font_size
)

logging.info("[Main] Vídeo listo: %s", video_path)

# === 6. Publicar en WhatsApp Web ============================================
publish(video_path, video_title)
