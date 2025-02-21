import csv
import re
import argparse
import os
import requests
import subprocess
import time

# Constantes globales
OUTPUT_FOLDER = "resources/texto"
CSV_HEADERS = ["ID", "Idea", "Nicho"]


def crear_prompt(nicho: str) -> str:
    """Genera el prompt para el modelo."""
    return f"""
        [INST]
        You are a professional storyteller and narrative designer specialized in {nicho} stories.
        Generate one unique short story, following these guidelines:
        - The story should be a complete narrative arc with a beginning, middle, and end.
        - Length: around 80 characters.
        - Include emotional elements and vivid descriptions.
        - Focus on creating cinematic, visual moments.
        - Perfect for video content and visual storytelling.
        - Suitable for short-form video narration.

        Just give me the story. I'll take care of the rest.
        [/INST]
    """


def procesar_respuesta(respuesta: list) -> str:
    """Procesa la respuesta del modelo y extrae la historia."""
    content = respuesta[0]["generated_text"].split("[/INST]")[-1].strip()
    pattern = r"Story:\s*(.*?)(?=\Z)"
    historia = re.search(pattern, content, re.DOTALL)
    return historia.group(1).strip() if historia else content.strip()


def guardar_idea_csv(ideas: list, nicho: str, archivo: str):
    """Guarda la idea generada en un archivo CSV."""
    with open(archivo, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        writer.writerow([1, ideas[0], nicho])


def formatear_csv(archivo: str):
    """Formatea el archivo CSV para manejar saltos de línea dentro de las celdas."""
    with open(archivo, "r", encoding="utf-8") as f:
        contenido = f.read()

    dentro_comillas = False
    nuevo_contenido = []
    for char in contenido:
        if char == '"':
            dentro_comillas = not dentro_comillas
        if dentro_comillas and char == "\n":
            nuevo_contenido.append(" ")
        else:
            nuevo_contenido.append(char)

    with open(archivo, "w", encoding="utf-8", newline="") as f:
        f.write("".join(nuevo_contenido))


def generar_ideas_ollama(nicho: str) -> list[str]:
    """Genera una idea utilizando el modelo de Ollama a través de su endpoint."""
    prompt = crear_prompt(nicho)
    url = "http://localhost:11434/api/generate"

    payload = {
        "model": "llama3.2",  # Especifica el modelo
        "prompt": prompt,
        "stream": False,  # Para obtener respuesta completa
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        # Ollama devuelve la respuesta en el campo 'response'
        texto_generado = data.get("response", "")

        # Procesamos la respuesta
        return [
            procesar_respuesta([{"generated_text": prompt + "\n" + texto_generado}])
        ]
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con Ollama: {e}")
        return []


def main(nicho: str):
    try:
        # Verificar si Ollama ya está corriendo y matarlo si es necesario
        subprocess.run(
            ["taskkill", "/F", "/IM", "ollama.exe"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("Iniciando Ollama limpio...")

        # Iniciar Ollama en segundo plano
        ollama_process = subprocess.Popen(
            ["ollama", "run", "llama2"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # Esperamos para que el endpoint se inicie
        time.sleep(5)

        # Generar ideas
        ideas = generar_ideas_ollama(nicho)
        if ideas:
            guardar_idea_csv(
                ideas, nicho, os.path.join(OUTPUT_FOLDER, f"idea_{nicho}.csv")
            )
            formatear_csv(os.path.join(OUTPUT_FOLDER, f"idea_{nicho}.csv"))
            print("Ideas generadas con éxito")

    except Exception as e:
        print(f"Error al generar ideas: {e}")

    finally:
        # Asegurarnos de que Ollama se cierre
        print("Finalizando Ollama...")
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
