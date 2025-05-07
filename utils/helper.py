import os
import datetime
import logging
import shutil
from dotenv import load_dotenv

def bootstrap(env_file: str = ".env", log_dir: str = "runs") -> None:
    """Carga .env y configura el logger global."""
    load_dotenv(env_file)
    os.makedirs(log_dir, exist_ok=True)

    log_path = os.path.join(log_dir, "execution.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s – %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, mode="a", encoding="utf-8"),
        ],
    )
    logging.info("Logging ✔ → %s", log_path)

    # Silencia 'openai', 'httpx' y tráfico de agents
    for noisy in ("openai", "httpx", "httpcore", "agents.http"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def new_run_dir(root: str = "runs") -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(root, f"run_{ts}")
    os.makedirs(path, exist_ok=True)
    return path


def move_into(target_dir: str, *files: str) -> list[str]:
    """Mueve cada archivo a target_dir y devuelve la lista de nuevas rutas."""
    new_paths: list[str] = []
    for f in files:
        if f and os.path.exists(f):
            dest = os.path.join(target_dir, os.path.basename(f))
            shutil.move(f, dest)
            new_paths.append(dest)
    return new_paths
