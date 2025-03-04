import os
import csv
import time
import torch
import nltk
from typing import List, Optional
from nltk.corpus import stopwords
from diffusers import (
    BitsAndBytesConfig,
    SD3Transformer2DModel,
    StableDiffusion3Pipeline,
)


class ImageGenerator:
    """Clase encargada de generar imágenes a partir de prompts."""

    PROMPTS_DIR = "resources/prompts"
    IMAGE_DIR = "resources/imagenes"
    MODEL_ID = "stabilityai/stable-diffusion-3.5-medium"
    IMAGE_WIDTH = 576
    IMAGE_HEIGHT = 1024
    IMAGEN_QUALITY = 90

    def __init__(self):
        os.makedirs(self.IMAGE_DIR, exist_ok=True)

        # Asegurarse de que NLTK tenga los stopwords
        if not hasattr(nltk, "data") or not stopwords.fileids():
            nltk.download("stopwords")

    def configurar_modelo(self):
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

        model_nf4 = SD3Transformer2DModel.from_pretrained(
            self.MODEL_ID,
            subfolder="transformer",
            quantization_config=nf4_config,
            torch_dtype=torch.float16,
            use_safetensors=True,
        )

        pipe = StableDiffusion3Pipeline.from_pretrained(
            self.MODEL_ID,
            transformer=model_nf4,
            torch_dtype=torch.float16,
            use_safetensors=True,
        )
        pipe.enable_model_cpu_offload()
        pipe.enable_attention_slicing()

        return pipe

    def generar_imagenes_desde_prompts(
        self,
        nicho: str,
        pipe: StableDiffusion3Pipeline,
        base_seed: Optional[int] = None,
    ) -> List[str]:
        imagenes_ruta = []
        prompts_file = os.path.join(self.PROMPTS_DIR, f"prompts_{nicho}.csv")

        # Si no se proporciona seed, generamos uno aleatorio
        if base_seed is None:
            base_seed = torch.randint(0, 2**32 - 1, (1,)).item()

        # Leer prompts del CSV
        with open(prompts_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            prompts = [row["Prompt"] for row in reader]

        for idx, prompt in enumerate(prompts):
            # Usamos un seed derivado para cada imagen
            current_seed = base_seed + idx
            generator = torch.Generator(device="cuda").manual_seed(current_seed)

            with torch.inference_mode():
                imagen = pipe(
                    prompt,
                    num_inference_steps=50,
                    guidance_scale=7.0,
                    negative_prompt="text, watermark, low quality, cropped",
                    height=self.IMAGE_HEIGHT,
                    width=self.IMAGE_WIDTH,
                    max_sequence_length=77,
                    generator=generator,
                ).images[0]

            # Guardamos la imagen con su seed en los metadatos
            ruta_imagen = os.path.join(
                self.IMAGE_DIR, f"imagen_{idx + 1:03d}_{nicho}.jpeg"
            )
            metadata = f"seed:{current_seed}"
            imagen.save(
                ruta_imagen,
                quality=self.IMAGEN_QUALITY,
                optimize=True,
                comment=metadata.encode(),
            )
            imagenes_ruta.append(ruta_imagen)
            time.sleep(0.5)

        return imagenes_ruta

    def generate(self, nicho: str, seed: Optional[int] = None) -> List[str]:
        pipe = self.configurar_modelo()
        imagenes_rutas = self.generar_imagenes_desde_prompts(nicho, pipe, seed)
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
        return imagenes_rutas
