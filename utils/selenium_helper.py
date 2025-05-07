#!/usr/bin/env python3
# selenium_helper.py
# Adaptado de test_publish.py manteniendo exactamente la funcionalidad que funciona

import os
import time
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ---------------------------------------------------
# CONFIGURACIÓN DE PERFILES
# ---------------------------------------------------
DEFAULT_PROFILE = Path(__file__).parent.parent / "selenium_profile"
PROFILE_DIR = Path(os.getenv("WHATSAPP_PROFILE_DIR", str(DEFAULT_PROFILE)))
PROFILE_DIR.mkdir(exist_ok=True)  # se crea si no existe

CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH")  # opcionalmente pon tu ruta

# -------------------------------------------------------------------
# Función para crear un ChromeDriver (mantenida exactamente como en el original)
# -------------------------------------------------------------------
def _mk_driver(headless: bool) -> webdriver.Chrome:
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
    # usamos un profile propio para no tocar tu Chrome de siempre
    opts.add_argument(f"--user-data-dir={PROFILE_DIR}")
    opts.add_argument("--no-sandbox")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    if CHROMEDRIVER_PATH:
        svc = Service(CHROMEDRIVER_PATH)
        return webdriver.Chrome(service=svc, options=opts)
    else:
        return webdriver.Chrome(options=opts)

# -------------------------------------------------------------------
# Comprobar si está logueado (función exacta del test_publish.py)
# -------------------------------------------------------------------
def is_logged_in(driver):
    """Comprueba si el botón Chats está seleccionado"""
    try:
        btn = driver.find_element(By.CSS_SELECTOR,
            "button[aria-label='Chats'][data-navbar-item-selected='true']")
        return btn.is_displayed()
    except:
        return False

# -------------------------------------------------------------------
# Función principal de publicación (interfaz compatible con main.py)
# -------------------------------------------------------------------
def publish(video_path: str, caption: str) -> None:
    """Publica un video como estado en WhatsApp Web.
    
    Esta función mantiene la lógica exacta de test_publish.py que funciona correctamente.
    """
    video_abs = os.path.abspath(video_path)
    
    if not os.path.isfile(video_abs):
        logging.error("El video no existe en %s", video_abs)
        exit(1)
    
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

    try:
        # 2️⃣ Ir a Estados
        logging.info("▶️ Abriendo Estados...")
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button[aria-label='Estados']")
        )).click()
        time.sleep(2)

        # 3️⃣ Nuevo estado
        logging.info("▶️ Nuevo estado...")
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button[aria-label='Add Status']")
        )).click()
        time.sleep(2)

        # 4️⃣ Seleccionar Fotos y Videos
        logging.info("▶️ Seleccionando Fotos y Videos...")
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "li[data-animate-dropdown-item] span[data-icon='media-refreshed']")
        )).click()
        time.sleep(2)

        # 5️⃣ Subir video
        logging.info(f"▶️ Subiendo video: {video_abs}")
        input_el = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='file']")
        ))
        input_el.send_keys(video_abs)
        time.sleep(10)  # Tiempo crucial para la carga del video

        # 6️⃣ Preview y caption
        logging.info("🔎 Esperando preview de vídeo...")
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "video")
        ))
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
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "div[role='button'][aria-label='Enviar']")
        )).click()
        time.sleep(5)  # Espera importante para completar el envío
        logging.info("✅ Estado publicado correctamente.")
    finally:
        driver.quit()

# -------------------------------------------------------------------
# Función ensure_session para mantener compatibilidad por si acaso
# -------------------------------------------------------------------
def ensure_session(timeout: int = 60) -> webdriver.Chrome:
    """Asegura que existe una sesión de WhatsApp Web"""
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
        wait = WebDriverWait(driver, timeout)
        logging.info("🔍 Espera QR y login en UI…")
        wait.until(lambda d: is_logged_in(d))
        logging.info("✅ Login completado en UI.")
        time.sleep(2)
    
    return driver