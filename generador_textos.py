import csv
import re
import torch
import argparse
import os
from dotenv import load_dotenv
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    pipeline,
    BitsAndBytesConfig,
)

# Constantes globales
MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.1"
OUTPUT_FOLDER = "resources/texto"
CSV_HEADERS = ["ID", "Idea", "Nicho"]


def configurar_entorno():
    """Configura las variables de entorno y devuelve el token."""
    load_dotenv()
    token = os.getenv("HUGGINGFACE_TOKEN")
    if not token:
        raise ValueError("No se encontró el token de Hugging Face en el archivo .env")
    return token


def inicializar_modelo(token: str):
    """Inicializa y retorna el modelo y tokenizer con la configuración optimizada."""
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        token=token,
        quantization_config=quantization_config,
        device_map="auto",
        trust_remote_code=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, token=token)
    return model, tokenizer


def crear_prompt(nicho: str) -> str:
    """Genera el prompt para el modelo."""
    return f"""
        [INST]
        You are a professional storyteller and narrative designer specialized in {nicho} stories.
        Generate one unique short story, following these guidelines:
        - The story should be a complete narrative arc with a beginning, middle, and end.
        - Length: around 180 characters.
        - Include emotional elements and vivid descriptions.
        - Focus on creating cinematic, visual moments.
        - Perfect for video content and visual storytelling.
        - Suitable for short-form video narration.
        - Include specific details about settings, lighting, and atmosphere.

        Format the story exactly as follows:
        Story:
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


def generar_ideas(model, tokenizer, nicho: str):
    """Genera una idea utilizando el modelo."""
    generador = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device_map="gpu",
        torch_dtype=torch.float16,
    )

    respuesta = generador(
        crear_prompt(nicho),
        max_new_tokens=1024,
        do_sample=True,
        temperature=0.9,
        top_k=50,
        top_p=0.95,
        num_return_sequences=1,
        repetition_penalty=1.2,
    )

    return [procesar_respuesta(respuesta)]


def main(nicho: str):
    """Función principal que coordina todo el proceso."""
    token = configurar_entorno()
    model, tokenizer = inicializar_modelo(token)

    ideas = generar_ideas(model, tokenizer, nicho)
    guardar_idea_csv(ideas, nicho, os.path.join(OUTPUT_FOLDER, f"idea_{nicho}.csv"))
    formatear_csv(os.path.join(OUTPUT_FOLDER, f"idea_{nicho}.csv"))

    # Limpieza de memoria
    torch.cuda.empty_cache()
    torch.cuda.ipc_collect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador de ideas para historias")
    parser.add_argument("--nicho", required=True, help="Nicho o tema de las historias")
    args = parser.parse_args()
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    main(args.nicho)
