#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orquesta: búsqueda → imágenes → TTS → vídeo → publicación Whatsapp.
"""

import os
import logging
import time

from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import openai
from utils.helper import bootstrap, new_run_dir
from my_agents.websearch_agent import run as web_search
from my_agents.illustration_agent import run as make_images
from my_agents.tts_agent import run as make_audio
from my_agents.script_agent import run as make_script
from utils.selenium_helper import publish

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import textwrap

# === 0. Arranque =============================================================
bootstrap()
openai.api_key = os.getenv("OPENAI_API_KEY")

TOPIC      = os.getenv("WEB_SEARCH_TOPIC")
VOICE      = os.getenv("TTS_VOICE")
TTS_MODEL  = os.getenv("TTS_MODEL")
IMG_MODEL  = os.getenv("IMAGE_GEN_MODEL")
TEXT_MODEL = os.getenv("WEB_SEARCH_MODEL")
CAPTION_TEXT   = os.getenv("CAPTION_TEXT")
TTS_TONE   = os.getenv("TTS_TONE")
IMAGE_COUNT = int(os.getenv("IMAGE_COUNT"))
SCRIPT_MODEL = os.getenv("SCRIPT_MODEL")

# === 1. Directorio de ejecución ==============================================
run_dir = new_run_dir()
logging.info("[Main] Carpeta de ejecución: %s", run_dir)

# === 2. Buscar info en la web ===============================================
summary = web_search(TOPIC, TEXT_MODEL)
out_log = logging.getLogger("AGENTS_OUT")
out_log.info("[WebSearch]\n%s\n", summary) 

final_script = make_script(summary, SCRIPT_MODEL)
out_log.info("[ScriptAgent]\n%s\n", final_script)

# === 3. Ilustraciones ========================================================
img_files = make_images(summary, IMAGE_COUNT, run_dir)
out_log.info("[Illustration]\n%s\n", "\n".join(img_files))

# === 4. Texto + audio ========================================================
script = f"{final_script}"
audio_file = make_audio(
    script, VOICE, TTS_MODEL, os.path.join(run_dir, "voice.mp3")
)
out_log.info("[TTS]\n%s\n", script)             # ← texto enviado a voz
out_log.info("[Audio] %s", audio_file)

# === 5. Vídeo ================================================================
audio_clip = AudioFileClip(audio_file)
duration = audio_clip.duration / len(img_files)
base_clips = [ImageClip(p).set_duration(duration) for p in img_files]

def _split_script(text: str, parts: int) -> list[str]:
    words = text.split()
    size = max(1, len(words)//parts)
    segments = []
    for i in range(parts):
        start = i*size
        end = (i+1)*size if i<parts-1 else len(words)
        segments.append(' '.join(words[start:end]))
    return segments

# Generar subtítulos distribuidos usando PIL
segments = _split_script(script, len(base_clips))
clips = []
for img_clip, seg in zip(base_clips, segments):
    width, height = img_clip.size
    wrapped = textwrap.fill(seg, width=40)
    txt_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_img)
    # Configure subtitle font size and font
    subtitle_font_size = int(os.getenv("SUBTITLE_FONT_SIZE", "40"))
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            subtitle_font_size,
        )
    except Exception:
        font = ImageFont.load_default()
    ascent, descent = font.getmetrics()
    line_h = ascent + descent + 4
    text_h = line_h * (wrapped.count('\n') + 1)
    y = height - text_h - 10
    draw.multiline_text((10, y), wrapped, font=font, fill=(255,255,255,255))
    txt_clip = ImageClip(np.array(txt_img)).set_duration(img_clip.duration)
    # Create CAPTION_TEXT overlay at top-right
    cap_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    cdraw = ImageDraw.Draw(cap_img)
    try:
        cap_w, cap_h = font.getsize(CAPTION_TEXT)
    except Exception:
        cap_w, cap_h = font.getmask(CAPTION_TEXT).size
    margin = 10
    cdraw.text((width - cap_w - margin, margin), CAPTION_TEXT, font=font, fill=(255,255,255,255))
    cap_clip = ImageClip(np.array(cap_img)).set_duration(img_clip.duration)
    clips.append(CompositeVideoClip([img_clip, txt_clip, cap_clip]))
video_clip = concatenate_videoclips(clips, method="compose").set_audio(audio_clip)

video_path = os.path.join(run_dir, "status.mp4")
video_clip.write_videofile(video_path, fps=24, codec="libx264")
logging.info("[Main] Vídeo listo: %s", video_path)

# === 6. Publicar en WhatsApp Web ============================================
publish(video_path, CAPTION_TEXT)
