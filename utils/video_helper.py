#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Funciones auxiliares para la generación de videos
"""
import os
import logging
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    ImageClip, AudioFileClip, AudioClip, CompositeVideoClip,
    concatenate_videoclips, concatenate_audioclips, CompositeAudioClip
)

def _split_script(text: str, parts: int) -> list[str]:
    """Divide un texto en partes aproximadamente iguales (por palabras)"""
    words = text.split()
    size = max(1, len(words)//parts)
    segments = []
    for i in range(parts):
        start = i*size
        end = (i+1)*size if i<parts-1 else len(words)
        segments.append(' '.join(words[start:end]))
    return segments

def process_audio(audio_file, bg_music_dir="media"):
    """Procesa el archivo de audio: añade silencios, ajusta volumen y añade música de fondo si está disponible"""
    logging.info("Procesando audio para vídeo...")
    
    # Cargar parámetros de volumen y segmentos desde variables de entorno
    voice_vol = float(os.getenv("VOICE_VOLUME", "1.0"))
    music_vol = float(os.getenv("MUSIC_VOLUME", "1.2"))
    silence_dur = float(os.getenv("SILENCE_DURATION", "3"))
    
    # Cargar el audio principal
    voice_audio = AudioFileClip(audio_file)
    
    # Añadir silencios al principio y final
    silence = AudioClip(lambda t: 0, duration=silence_dur)
    audio_with_silence = concatenate_audioclips([silence, voice_audio, silence])
    
    # Ajustar volumen de la voz
    audio_with_silence = audio_with_silence.volumex(voice_vol)
    logging.info(f"Volumen de voz ajustado a {voice_vol}")
    
    # Duración total del audio con silencios
    total_duration = audio_with_silence.duration
    
    # Intentar usar música de fondo (si está disponible)
    try:
        # Obtener nombre de archivo de música de fondo
        bg_music_file = os.getenv("BACKGROUND_MUSIC_FILE")
        if not bg_music_file:
            return audio_with_silence
        
        # Ruta completa al archivo de música
        bg_music_path = os.path.join(bg_music_dir, bg_music_file)
        
        # Verificar si existe
        if not os.path.isfile(bg_music_path):
            logging.warning(f"No se encontró el archivo de música {bg_music_path}")
            return audio_with_silence
        
        # Duración del audio original (con silencios)
        logging.info(f"Duración total del audio: {total_duration:.2f} segundos")
        
        # Cargar la música de fondo
        bg_audio = AudioFileClip(bg_music_path)
        bg_duration = bg_audio.duration
        logging.info(f"Duración de la música de fondo: {bg_duration:.2f} segundos")
        
        # Crear varios clips si es necesario repetir la música
        if bg_duration < total_duration:
            logging.info(f"La música es más corta que el audio. Creando repeticiones.")
            
            # Generar las repeticiones necesarias de la música
            repeats_needed = int(total_duration / bg_duration) + 1
            bg_clips = []
            
            for i in range(repeats_needed):
                # Para cada repetición, crear un clip con el offset adecuado
                clip_start = i * bg_duration
                clip_end = min((i + 1) * bg_duration, total_duration)
                clip_duration = clip_end - clip_start
                
                if clip_duration <= 0:
                    break
                
                # Crear un subclip para esta parte
                bg_subclip = bg_audio.subclip(0, min(clip_duration, bg_duration))
                # Ajustar su posición de inicio
                bg_subclip = bg_subclip.set_start(clip_start)
                bg_clips.append(bg_subclip)
            
            # Combinar todos los clips de música con el mismo volumen
            bg_combined = CompositeAudioClip(bg_clips).volumex(music_vol)
        else:
            # La música es más larga que el audio, simplemente recortamos
            logging.info("La música es más larga que el audio. Recortando.")
            bg_combined = bg_audio.subclip(0, total_duration).volumex(music_vol)
        
        # Combinar la música con el audio principal
        logging.info(f"Combinando audio con música de fondo")
        final_audio = CompositeAudioClip([bg_combined, audio_with_silence])
        return final_audio
    
    except Exception as e:
        logging.error(f"Error procesando la música de fondo: {str(e)}")
        # En caso de error, devolver solo el audio con silencios
        return audio_with_silence

def generate_video(audio_file, img_files, script, translated_script=None, hubo_traduccion=False, 
                  caption_text="", run_dir=".", font_size=None):
    """
    Genera un video combinando imágenes, audio y subtítulos.
    
    Args:
        audio_file: Ruta al archivo de audio
        img_files: Lista de rutas a imágenes
        script: Texto del guion
        translated_script: Texto traducido del guion (opcional)
        hubo_traduccion: Booleano que indica si se tradujo el script
        caption_text: Texto a mostrar en la esquina superior derecha
        run_dir: Directorio donde se guardará el video
        font_size: Tamaño de fuente para los subtítulos
    
    Returns:
        Ruta al archivo de video generado
    """
    # Procesamiento de audio
    audio_clip = process_audio(audio_file)
    
    # Crear los clips de imagen con la duración calculada
    duration = audio_clip.duration / len(img_files)
    base_clips = [ImageClip(p).set_duration(duration) for p in img_files]
    logging.info(f"Duración por imagen: {duration:.2f} segundos para {len(img_files)} imágenes")
    
    # Generar subtítulos distribuidos
    segments = _split_script(script, len(base_clips))
    clips = []
    
    # Determinar si hay que usar traducción
    if hubo_traduccion and translated_script:
        translated_segments = _split_script(translated_script, len(base_clips))
    else:
        translated_segments = None
        hubo_traduccion = False
    
    # Tamaño de fuente de subtítulos
    subtitle_font_size = font_size if font_size else int(os.getenv("SUBTITLE_FONT_SIZE", "30"))
    
    # Verificar si estamos usando audio personalizado (en cuyo caso no mostramos subtítulos)
    using_custom_audio = os.getenv("USE_CUSTOM_AUDIO", "false").lower() == "true"
    
    # Si estamos usando audio personalizado, forzamos a que no se muestren subtítulos ni overlay
    if using_custom_audio:
        logging.info("Usando audio personalizado - no se mostrarán subtítulos ni overlay")
        use_overlay = False
        # Vaciamos el texto de los segmentos para que no se muestren subtítulos
        segments = [""] * len(base_clips)
        if translated_segments:
            translated_segments = [""] * len(base_clips)
    else:
        # Determinar si se debe usar overlay para los subtítulos normales
        use_overlay = os.getenv("USE_OVERLAY", "false").lower() == "true"
    
    # Bucle principal para procesar cada imagen
    for i, img_clip in enumerate(base_clips):
        seg = segments[i]
        tseg = translated_segments[i] if translated_segments else None
        
        width, height = img_clip.size
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                subtitle_font_size,
            )
        except Exception:
            font = ImageFont.load_default()
        
        if use_overlay:
            # --- Usar overlays para imágenes web ---
            frame_np = img_clip.get_frame(0).astype('uint8')
            canvas = Image.fromarray(frame_np)
            draw = ImageDraw.Draw(canvas, 'RGBA')
            
            # --- Subtítulo original (izquierda, mini-overlay ajustado) ---
            # Limitar el ancho del texto a menos de la mitad de la pantalla
            chars_per_line = 32  # Reducir para evitar solapamiento
            
            # Dar formato al texto y calcular dimensiones
            wrapped = textwrap.fill(seg, width=chars_per_line)
            lines = wrapped.split('\n')
            ascent, descent = font.getmetrics()
            line_h = ascent + descent + 4
            text_h = line_h * len(lines)
            
            # Calcular el ancho máximo de las líneas de texto
            max_line_width = 0
            for line in lines:
                line_width = font.getsize(line)[0] if hasattr(font, 'getsize') else font.getmask(line).size[0]
                max_line_width = max(max_line_width, line_width)
            
            # Posicionar en la parte inferior con margen izquierdo
            left_margin = 20
            y = height - text_h - 20  # 20px de margen inferior
            padding = 10  # Espacio extra alrededor del texto
            
            # Dibujar un mini-overlay ajustado al tamaño exacto del texto
            draw.rectangle([
                (left_margin - padding, y - padding),
                (left_margin + max_line_width + padding, y + text_h + padding)
            ], fill=(0, 0, 0, 100))  # Negro semitransparente
            
            # Dibujar el texto sobre el mini-overlay
            draw.multiline_text((left_margin, y), wrapped, font=font, fill=(255, 255, 255, 255))
            
            # Subtítulo traducido (derecha) si procede
            # --- Subtítulo traducido (derecha, mini-overlay ajustado) ---
            if hubo_traduccion and tseg:
                # Dar formato al texto y calcular dimensiones
                chars_per_line = 32  # Reducir para evitar solapamiento
                t_wrapped = textwrap.fill(tseg, width=chars_per_line)
                t_lines = t_wrapped.split('\n')
                t_text_h = line_h * len(t_lines)
                
                # Calcular el ancho máximo de las líneas de texto
                t_max_line_width = 0
                for line in t_lines:
                    line_width = font.getsize(line)[0] if hasattr(font, 'getsize') else font.getmask(line).size[0]
                    t_max_line_width = max(t_max_line_width, line_width)
                
                # Posicionar en la parte inferior derecha con margen
                right_margin = width - t_max_line_width - 20  # 20px de margen derecho
                t_y = height - t_text_h - 20  # 20px de margen inferior
                padding = 10  # Espacio extra alrededor del texto
                
                # Dibujar un mini-overlay ajustado al tamaño exacto del texto
                draw.rectangle([
                    (right_margin - padding, t_y - padding),
                    (right_margin + t_max_line_width + padding, t_y + t_text_h + padding)
                ], fill=(0, 0, 0, 100))  # Negro semitransparente
                
                # Dibujar el texto sobre el mini-overlay, en verde claro
                draw.multiline_text((right_margin, t_y), t_wrapped, font=font, fill=(200, 255, 200, 255))
            
            # CAPTION_TEXT (arriba derecha, con mini-overlay solo si USE_OVERLAY es true)
            if caption_text:
                try:
                    cap_w, cap_h = font.getsize(caption_text)
                except Exception:
                    cap_w, cap_h = font.getmask(caption_text).size
                
                # Márgenes y posición del texto
                margin = 10
                padding = 5  # Espacio extra alrededor del texto
                text_x = width - cap_w - margin
                text_y = margin
                
                # Dibujar un overlay rectangular mínimo solo si USE_OVERLAY es true
                if use_overlay:
                    draw.rectangle([
                        (text_x - padding, text_y - padding),
                        (text_x + cap_w + padding, text_y + cap_h + padding)
                    ], fill=(0, 0, 0, 120))  # Negro semitransparente
                
                # Dibujar el texto (siempre se muestra, con o sin overlay)
                draw.text((text_x, text_y), caption_text, font=font, fill=(255, 255, 255, 255))
            
            # Crear clip final
            img_clip_with_overlay = ImageClip(np.array(canvas)).set_duration(img_clip.duration)
            clips.append(img_clip_with_overlay)
        else:
            # --- Funcionamiento original para imágenes generadas por IA ---
            # Estos clips usan capas transparentes superpuestas
            
            # Subtítulo original (izquierda)
            half_width = width // 2  # Dividir la pantalla en dos mitades
            chars_per_line = 35  # Menos caracteres para evitar solapamiento
            
            wrapped = textwrap.fill(seg, width=chars_per_line)
            txt_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(txt_img)
            ascent, descent = font.getmetrics()
            line_h = ascent + descent + 4
            text_h = line_h * (wrapped.count('\n') + 1)
            y = height - text_h - 10
            draw.multiline_text((10, y), wrapped, font=font, fill=(255,255,255,255))
            txt_clip = ImageClip(np.array(txt_img)).set_duration(img_clip.duration)
            
            if hubo_traduccion and tseg:
                # Subtítulo traducido (derecha)
                half_width = width // 2  # Dividir la pantalla en dos mitades
                right_margin = half_width + 10  # Margen desde la mitad de la pantalla
                chars_per_line = 35  # Menos caracteres para evitar solapamiento
                
                t_wrapped = textwrap.fill(tseg, width=chars_per_line)
                t_lines = t_wrapped.split('\n')
                t_text_h = line_h * len(t_lines)
                t_y = height - t_text_h - 10
                t_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                t_draw = ImageDraw.Draw(t_img)
                
                # Posicionar texto alineado desde la mitad de la pantalla
                for j, line in enumerate(t_lines):
                    t_draw.text((right_margin, t_y + j*line_h), line, font=font, fill=(200,255,200,255))
                t_clip = ImageClip(np.array(t_img)).set_duration(img_clip.duration)
                
                # CAPTION_TEXT (con mini-overlay solo si USE_OVERLAY es true)
                cap_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                cdraw = ImageDraw.Draw(cap_img)
                try:
                    cap_w, cap_h = font.getsize(caption_text)
                except Exception:
                    cap_w, cap_h = font.getmask(caption_text).size
                
                # Márgenes y posición del texto
                margin = 10
                padding = 5  # Espacio extra alrededor del texto
                text_x = width - cap_w - margin
                text_y = margin
                
                # Dibujar un overlay rectangular mínimo solo si USE_OVERLAY es true
                if use_overlay:
                    cdraw.rectangle([
                        (text_x - padding, text_y - padding),
                        (text_x + cap_w + padding, text_y + cap_h + padding)
                    ], fill=(0, 0, 0, 120))  # Negro semitransparente
                
                # Dibujar el texto (siempre se muestra, con o sin overlay)
                cdraw.text((text_x, text_y), caption_text, font=font, fill=(255,255,255,255))
                cap_clip = ImageClip(np.array(cap_img)).set_duration(img_clip.duration)
                
                clips.append(CompositeVideoClip([img_clip, txt_clip, t_clip, cap_clip]))
            else:
                # Sin traducción, solo subtítulo original
                if caption_text:
                    # CAPTION_TEXT (arriba derecha, con mini-overlay solo si USE_OVERLAY es true)
                    cap_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                    cdraw = ImageDraw.Draw(cap_img)
                    try:
                        cap_w, cap_h = font.getsize(caption_text)
                    except Exception:
                        cap_w, cap_h = font.getmask(caption_text).size
                    
                    # Márgenes y posición del texto
                    margin = 10
                    padding = 5  # Espacio extra alrededor del texto
                    text_x = width - cap_w - margin
                    text_y = margin
                    
                    # Dibujar un overlay rectangular mínimo solo si USE_OVERLAY es true
                    if use_overlay:
                        cdraw.rectangle([
                            (text_x - padding, text_y - padding),
                            (text_x + cap_w + padding, text_y + cap_h + padding)
                        ], fill=(0, 0, 0, 120))  # Negro semitransparente
                    
                    # Dibujar el texto (siempre se muestra, con o sin overlay)
                    cdraw.text((text_x, text_y), caption_text, font=font, fill=(255,255,255,255))
                    cap_clip = ImageClip(np.array(cap_img)).set_duration(img_clip.duration)
                    
                    clips.append(CompositeVideoClip([img_clip, txt_clip, cap_clip]))
                else:
                    clips.append(CompositeVideoClip([img_clip, txt_clip]))
    
    # Concatenar todos los clips y añadir audio
    video_clip = concatenate_videoclips(clips, method="compose")
    video_clip = video_clip.set_audio(audio_clip)
    video_clip = video_clip.set_duration(audio_clip.duration)
    
    # Guardar el video
    video_path = os.path.join(run_dir, "status.mp4")
    video_clip.write_videofile(
        video_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
    )
    logging.info("Video generado y guardado en: %s", video_path)
    
    return video_path
