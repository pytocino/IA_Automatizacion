import requests
import os
import argparse
import re
import csv
import subprocess
import time
from pydub import AudioSegment

OUTPUT_FOLDER = "resources/prompts"
CSV_HEADERS = ["ID", "Prompt"]
TEXT_DIR = "resources/texto"


def obtener_duracion_audio(nicho: str) -> float:
    """Obtiene la duración del audio en segundos"""
    try:
        audio_path = os.path.join("resources/audio", f"audio_{nicho}.mp3")
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"No se encontró el archivo de audio: {audio_path}")

        audio = AudioSegment.from_mp3(audio_path)
        duracion_segundos = len(audio) / 1000  # Convertir de milisegundos a segundos
        return duracion_segundos
    except Exception as e:
        print(f"Error al obtener duración del audio: {e}")
        return 40  # Valor por defecto de 40 segundos (10 imágenes)


def crear_prompts(text: str, num_prompts: int):
    """Crea prompts a partir de un texto utilizando chain-of-thought para obtener diversidad visual."""
    return f"""
    [INST]
    You are a professional prompt engineer specialized in image prompts. First, internally analyze the following text to identify distinct visual themes, scenarios, characters, and emotions. Draw inspiration from successful, engaging content practices.
    Then, generate {num_prompts} concise, clear, and self-contained prompts that each describe a distinct image concept. 
    Ensure that each prompt is visually appealing, original, and suitable for generating unique, cinematic images.
    
    IMPORTANT: Do not include any part of your internal reasoning in the final output. Output only the final image prompts, each separated by a line break, with no numbering, bullet points, or extra formatting.
    
    Text:
    {text}
    [INST]
    """


def procesar_respuesta(respuesta: dict) -> str:
    """Procesa la respuesta del modelo y extrae los prompts generados"""
    # Obtener el texto generado de la respuesta
    content = respuesta.get("response", "").strip()
    # Eliminar las secciones <think></think>
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
    # Limpiar espacios extra y líneas vacías
    content = "\n".join(line.strip() for line in content.split("\n") if line.strip())
    return content


def guardar_prompts_csv(prompts: list, archivo: str):
    with open(archivo, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(CSV_HEADERS)
        for i, prompt in enumerate(prompts, 1):
            prompt_limpio = re.sub(r"^\d+\.\s*", "", prompt)
            writer.writerow([i, prompt_limpio])


def generar_prompts_deepseek(text: str, num_prompts: int):
    prompts = crear_prompts(text, num_prompts)
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "deepseek-r1:14b",
        "prompt": prompts,
        "stream": False,
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return procesar_respuesta(data)
    except requests.RequestException as e:
        print(f"Error al generar prompts: {e}")
        return []


def main(nicho: str):
    try:
        # Obtener duración del audio y calcular número de prompts
        duracion = obtener_duracion_audio(nicho)
        num_prompts = max(1, int(duracion // 4))  # Una imagen cada 4 segundos
        print(f"Duración del audio: {duracion:.2f} segundos")
        print(f"Generando {num_prompts} prompts...")

        csv_filename = os.path.join(TEXT_DIR, f"idea_{nicho}.csv")
        with open(csv_filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader)
            texto = row["Idea"]

        # Generamos la respuesta completa con el número calculado de prompts
        prompts_str = generar_prompts_deepseek(texto, num_prompts)
        if prompts_str:
            prompts_list = [p.strip() for p in prompts_str.splitlines() if p.strip()]
            archivo = os.path.join(OUTPUT_FOLDER, f"prompts_{nicho}.csv")
            guardar_prompts_csv(prompts_list, archivo)
    except Exception as e:
        print(f"Error al generar prompts: {e}")

    finally:
        subprocess.Popen(
            ["ollama", "stop", "deepseek-r1:14b"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        subprocess.run(
            ["taskkill", "/F", "/IM", "ollama.exe"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador de ideas para historias")
    parser.add_argument("--nicho", required=True, help="Nicho o tema de las historias")
    args = parser.parse_args()
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    main(args.nicho)
