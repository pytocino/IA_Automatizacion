import subprocess
import argparse
import logging
import json
import sys
import random
import time
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("log/automation.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


def ejecutar_script(script_name: str, args: list = None) -> bool:
    try:
        cmd = ["py", script_name]
        if args:
            cmd.extend(args)

        logging.info(f"Ejecutando {script_name}...")
        process = subprocess.run(cmd, check=True, text=True, capture_output=True)

        # Si hay algún error, lo registramos
        if process.returncode != 0:
            logging.error(
                f"Error en {script_name}. Revisa automation.log para más detalles"
            )
            return False

        return True

    except subprocess.CalledProcessError as e:
        logging.error(f"Error ejecutando {script_name}: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Automatización de generación de contenido"
    )
    parser.add_argument(
        "--config", default="config.json", help="Ruta al archivo de configuración"
    )
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = json.load(f)
        nichos = config.get("nichos", [])
        num_ideas = config.get("num_ideas", 1)

    nicho = random.choice(nichos)
    logging.info(f"Generando contenido para el nicho: {nicho}")

    # Lista de tareas a ejecutar
    tareas = [
        (
            "Generando texto",
            "./generador_textos.py",
            ["--nicho", nicho],
        ),
        ("Generando audio", "./generador_audios.py", ["--nicho", nicho]),
        ("Generando imágenes", "./generador_imagenes.py", ["--nicho", nicho]),
        ("Generando subtitulos", "./generador_subtitulos.py", ["--nicho", nicho]),
        ("Generando videos", "./generador_videos_subtitulados.py", ["--nicho", nicho]),
    ]

    # Barra de progreso principal
    with tqdm(total=len(tareas), desc="Progreso total", position=0) as pbar:
        for desc, script, args in tareas:
            # Actualizar descripción
            pbar.set_description(f"▶ {desc}")

            # Ejecutar script
            if not ejecutar_script(script, args):
                logging.error(f"Error en {desc}")
                break

            time.sleep(1)
            pbar.update(1)

    logging.info("¡Automatización completada!")


if __name__ == "__main__":
    main()
