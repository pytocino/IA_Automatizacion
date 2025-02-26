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


def crear_prompt(
    nicho: str, era: str = "", location: str = "", tone: str = "engaging"
) -> str:
    """
    Generates a prompt for an AI model using chain-of-thought reasoning to create visually engaging
    short-form narratives with historical or factual foundations.

    Parameters:
        nicho: str - The specific subject/niche for the story
        era: str - Optional historical period (e.g., "Victorian", "Ancient", "1980s")
        location: str - Optional geographical setting (e.g., "Mediterranean", "Aztec Empire")
        tone: str - Emotional tone of the narrative (default: "engaging")

    Returns:
        str - Formatted prompt for the model
    """
    return f"""
        [INST]
        You are a professional storyteller and narrative designer specialized in {nicho} stories with a factual or historical twist.
        
        First, internally analyze:
        1. The core historical or factual elements of {nicho} that would surprise most viewers
        2. Visual imagery that could be captured in short-form video format
        3. Emotional hooks that create immediate interest in {nicho}
        4. How to incorporate {era if era else "any relevant time period"} and {location if location else "appropriate geographical context"}
        5. Ways to maintain a {tone} tone while being educational
        
        Then, generate one unique micro-story following these guidelines:
        - Begin with a hook starting with "Did you know...?" to introduce a surprising or intriguing fact
        - Length: 40-50 words maximum.
        - Focus on creating cinematic, visual moments that viewers can easily imagine
        - Include one specific detail (date, name, number) for authenticity
        - Ensure historical accuracy while maintaining narrative intrigue
        - Avoid clichés and overly familiar historical references
        
        IMPORTANT: Output only the final micro-story text, without any explanation, reasoning, or title.
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


def generar_ideas_deepseek(nicho: str, era: str, location: str, tone: str) -> list[str]:
    """Genera una idea utilizando el modelo de Ollama a través de su endpoint."""
    prompt = crear_prompt(nicho, era, location, tone)
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
        # Procesamos la respuesta
        return [
            procesar_respuesta([{"generated_text": prompt + "\n" + texto_generado}])
        ]
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con Ollama: {e}")
        return []


def main(nicho: str, era: str = "", location: str = "", tone: str = "engaging"):
    """Función principal para generar ideas de historias."""
    try:
        subprocess.Popen(
            ["ollama", "run", "deepseek-r1:14b"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # Esperamos para que el endpoint se inicie
        time.sleep(8)

        # Generar ideas
        ideas = generar_ideas_deepseek(nicho, era, location, tone)
        if ideas:
            guardar_idea_csv(
                ideas, nicho, os.path.join(OUTPUT_FOLDER, f"idea_{nicho}.csv")
            )
            formatear_csv(os.path.join(OUTPUT_FOLDER, f"idea_{nicho}.csv"))
    except Exception as e:
        print(f"Error al generar ideas: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador de ideas para historias")
    parser.add_argument(
        "--nicho", default="", required=True, help="Nicho o tema de las historias"
    )
    parser.add_argument("--era", default="", help="Período histórico para la historia")
    parser.add_argument("--location", help="Ubicación geográfica para la historia")
    parser.add_argument(
        "--tone", default="engaging", help="Tono emocional de la narrativa"
    )
    args = parser.parse_args()
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    main(args.nicho, args.era, args.location, args.tone)
