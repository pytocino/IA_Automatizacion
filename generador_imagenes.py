import argparse
import csv
import os
import torch
import time
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
PROMPTS_DIR = "resources/prompts"
IMAGE_DIR = "resources/imagenes"
MODEL_ID = "stabilityai/stable-diffusion-3.5-medium"
IMAGE_WIDTH = 576
IMAGE_HEIGHT = 1024
IMAGEN_QUALITY = 90


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


def generar_imagenes_desde_prompts(
    nicho: str, pipe: StableDiffusion3Pipeline
) -> list[str]:
    """Genera imágenes basadas en los prompts pre-generados del CSV."""
    imagenes_ruta = []
    prompts_file = os.path.join(PROMPTS_DIR, f"prompts_{nicho}.csv")

    # Leer prompts del CSV
    with open(prompts_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        prompts = [row["Prompt"] for row in reader]

    for idx, prompt in enumerate(
        tqdm(prompts, desc="Generando imágenes", unit="imagen", position=1, leave=False)
    ):
        with torch.inference_mode():
            imagen = pipe(
                prompt,
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
        generar_imagenes_desde_prompts(nicho, pipe)
    except FileNotFoundError:
        print(f"No se encontró el archivo de prompts para el nicho: {nicho}")
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
