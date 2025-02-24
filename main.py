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
        if process.stdout:
            logging.info(process.stdout)
        if process.stderr:
            logging.warning(process.stderr)

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

    nicho = random.choice(nichos)
    logging.info(f"Generando contenido para el nicho: {nicho}")

    # Lista de tareas a ejecutar
    tareas = [
        (
            "Generando texto",
            "./generador_textos.py",
            [
                "--nicho",
                nicho["name"],
                "--era",
                random.choice(nicho["eras"]),
                "--location",
                random.choice(nicho["locations"]),
                "--tone",
                random.choice(nicho["tones"]),
            ],
        ),
        ("Generando audio", "./generador_audios.py", ["--nicho", nicho["name"]]),
        ("Generando prompts", "./generador_prompts.py", ["--nicho", nicho["name"]]),
        ("Generando imágenes", "./generador_imagenes.py", ["--nicho", nicho["name"]]),
        (
            "Generando subtitulos",
            "./generador_subtitulos.py",
            ["--nicho", nicho["name"]],
        ),
        (
            "Generando videos",
            "./generador_videos_subtitulados.py",
            ["--nicho", nicho["name"]],
        ),
    ]

    # Barra de progreso principal
    with tqdm(total=len(tareas), desc="Progreso total", position=0) as pbar:
        for desc, script, args in tareas:
            # Ejecutar script
            if not ejecutar_script(script, args):
                logging.error(f"Error en {desc}")
                break

            # Actualizar barra de progreso después de completar la ejecución
            pbar.update(1)
            pbar.set_description(f"✓ {desc}")

    logging.info("¡Automatización completada!")


if __name__ == "__main__":
    main()
