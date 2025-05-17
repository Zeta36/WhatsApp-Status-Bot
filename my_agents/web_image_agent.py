import os
import time
import uuid
import logging
import re
from pathlib import Path
from typing import List # Eliminado Dict, Any ya que no se usan directamente en lo restante
from io import BytesIO
from PIL import Image, UnidentifiedImageError

# Dependencia para el nuevo agente
from bing_image_downloader import downloader as bing_downloader
import shutil

# ===========================================================================
# Logger global
# ===========================================================================
log = logging.getLogger(__name__)

# ===========================================================================
# Constantes de directorios
# ===========================================================================
# MAX_RETRY y BACKOFF ya no se usan directamente por fetch_images_via_bing
# HEADERS tampoco se usa.
# WEB_SEARCH_MODEL tampoco se usa en este flujo simplificado.
MEDIA_DIR = Path(__file__).parent.parent / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

# ===========================================================================
# CLASE ImageSearchAgent
# ===========================================================================
class ImageSearchAgent:
    def __init__(self, base_output_dir="downloaded_images"):
        self.base_output_dir = base_output_dir
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"Directorio base para descargas de Bing (temporal o no): {self.base_output_dir}")

    def _cleanup_query_string(self, query: str) -> str:
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in invalid_chars:
            query = query.replace(char, '')
        return query.replace(" ", "_")

    def search_and_download(self, query: str, num_images: int = 5, adult_filter_off: bool = True, force_replace: bool = False, timeout: int = 60) -> List[str]:
        if not query:
            self.logger.error("La consulta de búsqueda no puede estar vacía.")
            return []

        os.makedirs(self.base_output_dir, exist_ok=True)

        self.logger.info(f"Iniciando descarga para la consulta: '{query}'")
        self.logger.info(f"Se intentarán descargar {num_images} imágenes en subdirectorios de: '{self.base_output_dir}'")

        # `bing_downloader` mantiene los espacios en el directorio que crea
        # No usa cleaned_query_for_foldername, usa el query original con espacios
        actual_download_folder = os.path.join(self.base_output_dir, query)

        if os.path.exists(actual_download_folder) and not force_replace:
            self.logger.info(f"El directorio '{actual_download_folder}' para la consulta '{query}' ya existe y force_replace es False.")
            pass
        elif os.path.exists(actual_download_folder) and force_replace:
            self.logger.info(f"Eliminando directorio existente '{actual_download_folder}' debido a force_replace=True.")
            try:
                shutil.rmtree(actual_download_folder)
            except Exception as e:
                self.logger.error(f"No se pudo eliminar el directorio '{actual_download_folder}': {e}")

        downloaded_image_paths = []
        try:
            bing_downloader.download(
                query,
                limit=num_images,
                output_dir=str(self.base_output_dir),
                adult_filter_off=adult_filter_off,
                force_replace=force_replace,
                timeout=timeout,
                verbose=True  # Activar para ver más detalles del error
            )

            if os.path.exists(actual_download_folder):
                for item in os.listdir(actual_download_folder):
                    item_path = os.path.join(actual_download_folder, item)
                    if os.path.isfile(item_path) and any(item.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']):
                        downloaded_image_paths.append(os.path.abspath(item_path))
                self.logger.info(f"Se encontraron {len(downloaded_image_paths)} imágenes para '{query}' en '{actual_download_folder}'.")
            else:
                self.logger.warning(f"El directorio esperado '{actual_download_folder}' no fue creado por la librería o está vacío.")

        except Exception as e:
            self.logger.exception(f"Error durante la descarga de Bing para '{query}': {e}")
            return []

        return downloaded_image_paths[:num_images]

        return downloaded_image_paths[:num_images] # Asegura devolver máximo num_images

# ---------------------------------------------------------------------------
# Utilidades de imagen
# ---------------------------------------------------------------------------
def _process_downloaded_image(source_image_path: Path, final_out_dir: Path, desired_width: int = 1024, aspect_ratio: float = 16/9) -> str:
    """
    Abre una imagen desde source_image_path, la redimensiona a proporción 16:9, y la guarda en final_out_dir.
    Retorna la ruta de la imagen guardada o una cadena vacía si falla.
    """
    try:
        log.debug("Procesando imagen: %s, directorio final=%s", source_image_path, final_out_dir)
        img = Image.open(source_image_path)

        # Convertir cualquier modo de imagen a RGB (incluido escala de grises)
        if img.mode != 'RGB':
            log.debug("Convirtiendo imagen de modo %s a RGB.", img.mode)
            img = img.convert('RGB')

        log.debug("Imagen original tamaño: %dx%d, modo: %s", img.width, img.height, img.mode)

        if img.width == 0 or img.height == 0:
            log.error("Imagen fuente tiene dimensiones cero: %s", source_image_path)
            return ""
            
        # Calcular la altura deseada basada en la proporción 16:9
        desired_height = int(desired_width / aspect_ratio)
        log.debug(f"Dimensiones objetivo para proporción {aspect_ratio:.2f}: {desired_width}x{desired_height}")
        
        # Primero redimensionar manteniendo la proporción original
        if img.width / img.height > aspect_ratio:  # Imagen más ancha que 16:9
            # Redimensionar por altura
            new_width = int(img.width * (desired_height / img.height))
            img = img.resize((new_width, desired_height), Image.LANCZOS)
            # Recortar el exceso de ancho (centrado)
            left = (new_width - desired_width) // 2
            img = img.crop((left, 0, left + desired_width, desired_height))
            log.debug(f"Imagen más ancha: redimensionada a {new_width}x{desired_height}, recortada a {desired_width}x{desired_height}")
        else:  # Imagen más alta que 16:9 o exacta
            # Redimensionar por ancho
            new_height = int(img.height * (desired_width / img.width))
            img = img.resize((desired_width, new_height), Image.LANCZOS)
            # Recortar el exceso de altura (centrado)
            top = (new_height - desired_height) // 2
            img = img.crop((0, top, desired_width, top + desired_height))
            log.debug(f"Imagen más alta: redimensionada a {desired_width}x{new_height}, recortada a {desired_width}x{desired_height}")

        # Nombre de archivo único en el directorio de salida final
        path = final_out_dir / f"img_{int(time.time())}_{uuid.uuid4().hex}.jpg"

        final_out_dir.mkdir(parents=True, exist_ok=True)
        img.save(path, format="JPEG", quality=90) # Calidad JPEG
        log.debug("Imagen procesada y guardada en %s", path)
        return str(path)
    except UnidentifiedImageError:
        log.error("No se pudo identificar el archivo (corrupto o no es imagen): %s", source_image_path)
        return ""
    except Exception:
        log.exception(f"Error en _process_downloaded_image procesando {source_image_path}")
        return ""

# ---------------------------------------------------------------------------
# Función de agente usando ImageSearchAgent (Bing)
# ---------------------------------------------------------------------------
def fetch_images_via_bing(topic: str, count: int, out_dir: str) -> List[str]:
    log.info("=== BÚSQUEDA DE IMÁGENES (Bing): %s ===", topic)

    final_out_path = Path(out_dir)
    # No es necesario crear final_out_path aquí, _process_downloaded_image lo hará.

    # Directorio temporal para las descargas de bing-image-downloader
    temp_bing_download_dir = final_out_path / f"bing_temp_{uuid.uuid4().hex[:8]}"
    # ImageSearchAgent se encargará de crear temp_bing_download_dir si es necesario

    log.debug(f"Directorio temporal para descargas de Bing: {temp_bing_download_dir}")

    agent = ImageSearchAgent(base_output_dir=str(temp_bing_download_dir))

    # force_replace=True es útil para dir temporales para asegurar descargas frescas si se reejecuta.
    raw_downloaded_paths = agent.search_and_download(topic, num_images=count, force_replace=True)

    if not raw_downloaded_paths:
        log.warning(f"ImageSearchAgent no devolvió rutas para '{topic}'.")
        # Intentar limpiar el directorio temporal si se creó y está vacío o falló
        if temp_bing_download_dir.exists():
            try:
                shutil.rmtree(temp_bing_download_dir)
                log.debug(f"Directorio temporal {temp_bing_download_dir} eliminado (sin imágenes descargadas).")
            except Exception as e_clean:
                log.error(f"Error eliminando directorio temporal {temp_bing_download_dir}: {e_clean}")
        return []

    log.info(f"ImageSearchAgent descargó {len(raw_downloaded_paths)} imágenes en bruto.")

    processed_image_paths: List[str] = []
    for i, raw_path_str in enumerate(raw_downloaded_paths):
        if len(processed_image_paths) >= count: # No procesar más de 'count'
            break
        log.debug(f"Procesando imagen {i+1}/{len(raw_downloaded_paths)}: {raw_path_str}")
        # Usar proporción 16:9 para procesar las imágenes
        processed_path = _process_downloaded_image(Path(raw_path_str), final_out_path, desired_width=1024, aspect_ratio=16/9)
        if processed_path:
            processed_image_paths.append(processed_path)

    # Limpiar el directorio temporal de descargas de Bing
    try:
        shutil.rmtree(temp_bing_download_dir)
        log.debug(f"Directorio temporal {temp_bing_download_dir} eliminado exitosamente.")
    except Exception as e:
        log.error(f"Error eliminando el directorio temporal {temp_bing_download_dir}: {e}")

    log.info("Imágenes procesadas y guardadas desde Bing: %d/%d", len(processed_image_paths), count)
    return processed_image_paths