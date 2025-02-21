import argparse
import csv
import os
import subprocess
import torch
import time
import random
import nltk
from nltk.corpus import stopwords
from diffusers import (
    BitsAndBytesConfig,
    SD3Transformer2DModel,
    StableDiffusion3Pipeline,
)
from tqdm import tqdm

if not stopwords.fileids():
    nltk.download("stopwords")

# Configuración global
AUDIO_DIR = "resources/audio"
IMAGE_DIR = "resources/imagenes"
TEXT_DIR = "resources/texto"
MODEL_ID = "stabilityai/stable-diffusion-3.5-medium"
IMAGE_WIDTH = 576
IMAGE_HEIGHT = 1024
IMAGEN_QUALITY = 90
FRAMES_PER_SECOND = 4
# 576, 1024


# Configuración del modelo
def configurar_modelo():
    # Configuración de memoria y precisión para CUDA
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    torch.backends.cudnn.benchmark = True

    # Configuración de cuantización
    nf4_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    # Cargar modelo
    model_nf4 = SD3Transformer2DModel.from_pretrained(
        MODEL_ID,
        subfolder="transformer",
        quantization_config=nf4_config,
        torch_dtype=torch.float16,
        use_safetensors=True,
    )

    pipe = StableDiffusion3Pipeline.from_pretrained(
        MODEL_ID,
        transformer=model_nf4,
        torch_dtype=torch.float16,
        use_safetensors=True,
    )
    pipe.enable_model_cpu_offload()
    pipe.enable_attention_slicing()

    return pipe


def obtener_duracion_audio(audio_path: str) -> float:
    """Obtiene la duración de un archivo de audio usando ffprobe."""
    comando = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        audio_path,
    ]
    duracion = float(subprocess.check_output(comando).decode().strip())
    return duracion


def generar_prompt_optimizado(palabras_clave: list[str]) -> str:
    """Genera un prompt optimizado para la generación de imágenes."""
    num_palabras = random.randint(4, 9)
    prompt_palabras = random.sample(
        palabras_clave, min(num_palabras, len(palabras_clave))
    )
    return f"{' '.join(prompt_palabras)}, cinematic, detailed, high quality"


def procesar_texto(texto: str) -> list[str]:
    """Procesa el texto para obtener palabras clave relevantes."""
    palabras = [p.strip() for p in texto.lower().split() if p.strip()]
    return [p for p in palabras if p not in set(stopwords.words("english"))]


def generar_imagenes_dinamicamente(
    texto: str, duracion_audio: float, nicho: str, pipe: StableDiffusion3Pipeline
) -> list[str]:
    """Genera imágenes basadas en el texto y la duración del audio."""
    num_imagenes = max(1, int(duracion_audio / FRAMES_PER_SECOND))
    palabras_clave = procesar_texto(texto)
    imagenes_ruta = []

    for idx in tqdm(range(num_imagenes), desc="Generando imágenes", unit="imagen"):
        prompt_optimizado = generar_prompt_optimizado(palabras_clave)

        with torch.inference_mode():
            imagen = pipe(
                prompt_optimizado,
                num_inference_steps=30,
                guidance_scale=7.0,
                negative_prompt="text, watermark, low quality, cropped",
                height=IMAGE_HEIGHT,
                width=IMAGE_WIDTH,
                max_sequence_length=77,
            ).images[0]

        ruta_imagen = os.path.join(IMAGE_DIR, f"imagen_{idx + 1:03d}_{nicho}.jpeg")
        imagen.save(ruta_imagen, quality=IMAGEN_QUALITY, optimize=True)
        imagenes_ruta.append(ruta_imagen)
        time.sleep(0.5)

    return imagenes_ruta


def main(nicho):
    os.makedirs(IMAGE_DIR, exist_ok=True)
    pipe = configurar_modelo()
    try:
        csv_filename = os.path.join(TEXT_DIR, f"idea_{nicho}.csv")
        with open(csv_filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader)
            texto = row["Idea"]

        audio_path = os.path.join(AUDIO_DIR, f"audio_{nicho}.mp3")
        duracion_audio = obtener_duracion_audio(audio_path)

        generar_imagenes_dinamicamente(texto, duracion_audio, nicho, pipe)

    except FileNotFoundError:
        print(f"No se encontró el archivo CSV: {csv_filename}")
    except StopIteration:
        print("El archivo CSV está vacío")
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
    finally:
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador de imágenes para historias")
    parser.add_argument("--nicho", required=True, help="Nicho o tema de las historias")
    args = parser.parse_args()
    main(args.nicho)
