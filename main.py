import subprocess
import argparse
import logging
import json
import sys
import random

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("automation.log"), logging.StreamHandler(sys.stdout)],
)


def ejecutar_script(script_name: str, args: list = None) -> bool:
    try:
        cmd = ["py", script_name]
        if args:
            cmd.extend(args)

        process = subprocess.run(cmd, check=True, text=True, capture_output=True)

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
        num_ideas = config.get("num_ideas", 1)

    nicho = random.choice(nichos)
    logging.info(f"Generando contenido para el nicho: {nicho}")

    # 1. Generar texto
    ejecutar_script(
        "./generador_textos.py", ["--nicho", nicho, "--num_ideas", str(num_ideas)]
    )

    # 2. Generar audio
    ejecutar_script("./generador_audios.py")

    # 3. Generar videos
    ejecutar_script("./generador_videos.py")

    logging.info("¡Automatización completada!")


if __name__ == "__main__":
    main()
