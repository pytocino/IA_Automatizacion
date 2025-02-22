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
        - Length: around 80 characters.
        - Focus on creating cinematic, visual moments.
        - Perfect for video content and visual story time.
        - Suitable for short-form video narration.

        Just give me the text, not even the title. I'll take care of the rest.
        [/INST]
    """


def procesar_respuesta(respuesta: list) -> str:
    """Procesa la respuesta del modelo y extrae la historia.

    Args:
        respuesta (list): Lista con la respuesta del modelo

    Returns:
        str: Historia procesada sin las etiquetas de pensamiento
    """
    content = respuesta[0]["generated_text"].split("[/INST]")[-1].strip()

    # Eliminar el contenido entre las etiquetas <think></think>
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)

    # Limpiar espacios extra y líneas en blanco
    content = re.sub(r"\n\s*\n", "\n", content.strip())

    return content.strip()


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


def generar_ideas_deepseek(nicho: str) -> list[str]:
    """Genera una idea utilizando el modelo de Ollama a través de su endpoint."""
    prompt = crear_prompt(nicho)
    url = "http://localhost:11434/api/generate"

    payload = {
        "model": "deepseek-r1:14b",  # Especifica el modelo
        "prompt": prompt,
        "stream": False,  # Para obtener respuesta completa
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        # Ollama devuelve la respuesta en el campo 'response'
        texto_generado = data.get("response", "")
        print(f"Texto generado: {texto_generado}")
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
        subprocess.Popen(
            ["ollama", "run", "deepseek-r1:14b"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # Esperamos para que el endpoint se inicie
        time.sleep(8)

        # Generar ideas
        ideas = generar_ideas_deepseek(nicho)
        if ideas:
            guardar_idea_csv(
                ideas, nicho, os.path.join(OUTPUT_FOLDER, f"idea_{nicho}.csv")
            )
            formatear_csv(os.path.join(OUTPUT_FOLDER, f"idea_{nicho}.csv"))
            print("Ideas generadas con éxito")
    except Exception as e:
        print(f"Error al generar ideas: {e}")

    finally:
        subprocess.Popen(
            ["ollama", "stop", "deepseek-r1:14b"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # Asegurarnos de que Ollama se cierre
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
