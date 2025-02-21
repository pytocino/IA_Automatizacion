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
OUTPUT_FILE = "ideas_generadas.csv"
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


def crear_prompt(nicho: str, num_ideas: int) -> str:
    """Genera el prompt para el modelo."""
    return f"""
        [INST]
        You are a professional storyteller and narrative designer specialized in {nicho} stories.
        Make each story unique and engaging, focusing on {nicho} themes.

        Generate {num_ideas} unique short stories, following these guidelines:
        - Each story should be a complete narrative arc with a beginning, middle, and end.
        - Length: around 180 characters.
        - Include emotional elements and vivid descriptions.
        - Focus on creating cinematic, visual moments.
        - Perfect for video content and visual storytelling.
        - Suitable for short-form video narration.
        - Include specific details about settings, lighting, and atmosphere.

        Format each story exactly as follows (each story must be separated):
        Title:
        Story:
        [/INST]
    """


def procesar_respuesta(respuesta: list, num_ideas: int) -> list:
    """Procesa la respuesta del modelo y extrae las historias."""
    content = respuesta[0]["generated_text"].split("[/INST]")[-1].strip()
    pattern = r"Title:\s*(.*?)\s*Story:\s*(.*?)(?=\s*Title:|\Z)"
    historias = re.findall(pattern, content, re.DOTALL)
    return [
        re.sub(r"^.*?:\s*", "", historia.strip(), 1)
        for titulo, historia in historias[:num_ideas]
    ]


def guardar_ideas_csv(ideas: list, nicho: str, archivo: str):
    """Guarda las ideas generadas en un archivo CSV."""
    with open(archivo, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        for idx, idea in enumerate(ideas, 1):
            writer.writerow([idx, idea, nicho])


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


def generar_ideas(model, tokenizer, nicho: str, num_ideas: int):
    """Genera las ideas utilizando el modelo."""
    generador = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device_map="auto",
        torch_dtype=torch.float16,
    )

    respuesta = generador(
        crear_prompt(nicho, num_ideas),
        max_new_tokens=1024,
        do_sample=True,
        temperature=0.85,
        top_k=50,
        top_p=0.95,
        num_return_sequences=1,
        repetition_penalty=1.2,
    )

    return procesar_respuesta(respuesta, num_ideas)


def main(nicho: str, num_ideas: int):
    """Función principal que coordina todo el proceso."""
    token = configurar_entorno()
    model, tokenizer = inicializar_modelo(token)

    ideas = generar_ideas(model, tokenizer, nicho, num_ideas)
    guardar_ideas_csv(ideas, nicho, OUTPUT_FILE)
    formatear_csv(OUTPUT_FILE)

    # Limpieza de memoria
    torch.cuda.empty_cache()
    torch.cuda.ipc_collect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador de ideas para historias")
    parser.add_argument("--nicho", required=True, help="Nicho o tema de las historias")
    parser.add_argument(
        "--num_ideas", type=int, required=True, help="Número de ideas a generar"
    )
    args = parser.parse_args()
    main(args.nicho, args.num_ideas)
