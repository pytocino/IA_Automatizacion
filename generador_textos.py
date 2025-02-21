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

# Cargar variables de entorno
load_dotenv()
token = os.getenv("HUGGINGFACE_TOKEN")

if not token:
    raise ValueError("No se encontró el token de Hugging Face en el archivo .env")

# Configuración avanzada de optimización de memoria
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16, bnb_4bit_quant_type="nf4"
)

# Carga del modelo con configuración optimizada
model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.1",
    token=token,
    quantization_config=quantization_config,
    device_map="auto",
    trust_remote_code=True,
)

tokenizer = AutoTokenizer.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.1", token=token
)


def crear_prompt(nicho: str, num_ideas: int) -> str:
    return f"""
[INST]
You are a professional storyteller and narrative designer specialized in {nicho} stories.
Make each story unique and engaging, focusing on {nicho} themes.

Generate {num_ideas} unique short stories, following these guidelines:
- Each story should be a complete narrative arc with a beginning, middle, and end.
- Length: around 200 characters.
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
    content = respuesta[0]["generated_text"].split("[/INST]")[-1].strip()
    pattern = r"Title:\s*(.*?)\s*Story:\s*(.*?)(?=\s*Title:|\Z)"
    historias = re.findall(pattern, content, re.DOTALL)
    return [
        re.sub(r"^.*?:\s*", "", historia.strip(), 1)
        for titulo, historia in historias[:num_ideas]
    ]


def main(nicho, num_ideas):
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

    ideas = procesar_respuesta(respuesta, num_ideas)

    with open("ideas_generadas.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Idea", "Nicho"])
        for idx, idea in enumerate(ideas, 1):
            writer.writerow([idx, idea, nicho])

    torch.cuda.empty_cache()
    torch.cuda.ipc_collect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--nicho", required=True)
    parser.add_argument("--num_ideas", type=int, required=True)
    args = parser.parse_args()
    main(args.nicho, args.num_ideas)
