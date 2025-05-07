#!/usr/bin/env python3
# test_publish.py
# Script de prueba para publicar el video de estado en WhatsApp Web
# Inicia en headless para chequear sesión; si hace falta QR usa ventana visible y continúa ahí.

import os
import time
import logging
import argparse

from selenium_helper import _mk_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Configurar logging
tlogging = logging.getLogger()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s – %(message)s")

# Parsear argumentos
parser = argparse.ArgumentParser(
    description="Publica un video como estado en WhatsApp Web"
)
parser.add_argument("video_path", help="Ruta al archivo MP4 a publicar")
parser.add_argument("--caption", default="prueba", help="Texto de caption para el estado")
args = parser.parse_args()

video_path = os.path.abspath(args.video_path)
caption    = args.caption

if not os.path.isfile(video_path):
    logging.error("El video no existe en %s", video_path)
    exit(1)


def is_logged_in(driver):
    """Comprueba si el botón Chats está seleccionado"""
    try:
        btn = driver.find_element(By.CSS_SELECTOR,
            "button[aria-label='Chats'][data-navbar-item-selected='true']")
        return btn.is_displayed()
    except:
        return False


def publish_visible(video_path: str, caption: str) -> None:
    # 1️⃣ Intento headless para validar sesión
    driver = _mk_driver(headless=True)
    driver.get("https://web.whatsapp.com")
    wait = WebDriverWait(driver, 15)
    try:
        logging.info("🔍 Comprobando sesión en headless…")
        wait.until(lambda d: is_logged_in(d))
        logging.info("✅ Sesión activa en headless.")
    except TimeoutException:
        # Si no está logueado, pasar a UI visible
        logging.info("⚠️ No logueado. Abriendo UI para escanear QR…")
        driver.quit()
        driver = _mk_driver(headless=False)
        driver.get("https://web.whatsapp.com")
        wait = WebDriverWait(driver, 60)
        logging.info("🔍 Espera QR y login en UI…")
        wait.until(lambda d: is_logged_in(d))
        logging.info("✅ Login completado en UI.")
        time.sleep(2)

    # 2️⃣ Ir a Estados
    logging.info("▶️ Abriendo Estados...")
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Estados']"))).click()
    time.sleep(2)

    # 3️⃣ Nuevo estado
    logging.info("▶️ Nuevo estado...")
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Add Status']"))).click()
    time.sleep(2)

    # 4️⃣ Seleccionar Fotos y Videos
    logging.info("▶️ Seleccionando Fotos y Videos...")
    wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "li[data-animate-dropdown-item] span[data-icon='media-refreshed']")
    )).click()
    time.sleep(2)

    # 5️⃣ Subir video
    logging.info(f"▶️ Subiendo video: {video_path}")
    input_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
    input_el.send_keys(video_path)
    time.sleep(10)

    # 6️⃣ Preview y caption
    logging.info("🔎 Esperando preview de vídeo...")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "video")))
    time.sleep(1)
    logging.info("✏️ Escribiendo caption...")
    try:
        cap_el = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            "div[contenteditable='true'][aria-label='Añade un comentario']"
        )))
        cap_el.clear()
        cap_el.send_keys(caption)
        time.sleep(1)
    except Exception:
        logging.warning("Pie de foto no disponible.")

    # 7️⃣ Enviar estado
    logging.info("▶️ Enviando estado...")
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div[role='button'][aria-label='Enviar']"))).click()
    time.sleep(5)
    logging.info("✅ Estado publicado correctamente.")

    driver.quit()


if __name__ == "__main__":
    publish_visible(video_path, caption)
