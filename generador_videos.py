import csv
import os
import subprocess
import torch
from PIL import Image
import time
import tempfile
import random
import nltk
from nltk.corpus import stopwords
from diffusers import (
    BitsAndBytesConfig,
    SD3Transformer2DModel,
    StableDiffusion3Pipeline,
)

# Configurar directorios
AUDIO_DIR = "audios"
IMAGE_DIR = "imagenes"
VIDEO_DIR = "videos"
SUBTITLES_DIR = "subtitulos"

# Cargar modelo Stable Diffusion 3
model_id = "stabilityai/stable-diffusion-3.5-medium"

# Configuración de memoria y precisión para CUDA
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True
torch.backends.cudnn.benchmark = True

# Cuantización a 4-bits
nf4_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)
model_nf4 = SD3Transformer2DModel.from_pretrained(
    model_id,
    subfolder="transformer",
    quantization_config=nf4_config,
    torch_dtype=torch.float16,
    use_safetensors=True,
)
pipe = StableDiffusion3Pipeline.from_pretrained(
    model_id,
    transformer=model_nf4,
    torch_dtype=torch.float16,
    use_safetensors=True,
)
pipe.enable_model_cpu_offload()
pipe.enable_attention_slicing()


def obtener_duracion_audio(audio_path: str) -> float:
    duracion = float(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                audio_path,
            ]
        )
        .decode()
        .strip()
    )
    return duracion


def generar_imagenes_dinamicamente(
    idea_texto: str, audio_path: str, nicho: str
) -> list[str]:
    pipe.enable_attention_slicing()
    width, height = 576, 1024  # Dimensiones para ratio 9:16

    duracion_audio = obtener_duracion_audio(audio_path)
    num_imagenes = max(1, int(duracion_audio / 4))

    imagenes_ruta = []
    palabras_clave = [p.strip() for p in idea_texto.lower().split() if p.strip()]
    palabras_clave = [
        p for p in palabras_clave if p not in set(stopwords.words("english"))
    ]

    for idx in range(num_imagenes):
        num_palabras = random.randint(4, 9)
        prompt_palabras = random.sample(
            palabras_clave, min(num_palabras, len(palabras_clave))
        )
        prompt_optimizado = (
            f"{' '.join(prompt_palabras)}, cinematic, detailed, high quality"
        )

        with torch.inference_mode():
            imagen = pipe(
                prompt_optimizado,
                num_inference_steps=20,
                guidance_scale=7.0,
                negative_prompt="text, watermark, low quality, cropped",
                height=height,
                width=width,
                max_sequence_length=77,
            ).images[0]

        torch.cuda.empty_cache()
        ruta_imagen = os.path.join(IMAGE_DIR, f"imagen_{idx + 1}_{nicho}.webp")
        imagen.save(ruta_imagen, quality=90, optimize=True)
        imagenes_ruta.append(ruta_imagen)
        time.sleep(0.5)

    return imagenes_ruta


def crear_archivo_srt(
    texto: str, duracion_audio: float, duracion_por_imagen: float
) -> str:
    """
    Crea un archivo SRT con el texto dividido según la duración de cada imagen
    """
    num_bloques = int(duracion_audio / duracion_por_imagen)
    palabras = texto.split()
    palabras_por_bloque = len(palabras) // num_bloques

    srt_content = ""
    for i in range(num_bloques):
        # Usar duracion_por_imagen para los tiempos
        inicio = i * duracion_por_imagen
        fin = (i + 1) * duracion_por_imagen

        # Calcular el rango de palabras para este bloque
        inicio_palabras = i * palabras_por_bloque
        fin_palabras = (
            (i + 1) * palabras_por_bloque if i < num_bloques - 1 else len(palabras)
        )
        texto_bloque = " ".join(palabras[inicio_palabras:fin_palabras])

        # Formatear tiempo en formato HH:MM:SS,mmm
        inicio_seg = int(inicio)
        inicio_ms = int((inicio - inicio_seg) * 1000)
        fin_seg = int(fin)
        fin_ms = int((fin - fin_seg) * 1000)

        inicio_str = f"{inicio_seg//3600:02d}:{(inicio_seg%3600)//60:02d}:{inicio_seg%60:02d},{inicio_ms:03d}"
        fin_str = f"{fin_seg//3600:02d}:{(fin_seg%3600)//60:02d}:{fin_seg%60:02d},{fin_ms:03d}"

        srt_content += f"{i+1}\n{inicio_str} --> {fin_str}\n{texto_bloque}\n\n"

    srt_path = os.path.join(SUBTITLES_DIR, "subtitulos.srt")

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    return srt_path


def crear_video_ffmpeg(
    image_paths: list, audio_path: str, id_idea: str, nicho: str, texto: str
) -> str:
    with Image.open(image_paths[0]) as img:
        width, height = img.size

    duracion_audio = obtener_duracion_audio(audio_path)
    duracion_por_imagen = duracion_audio / len(image_paths)
    output_path = os.path.join(VIDEO_DIR, f"video_{id_idea}_{nicho}.mp4")

    # Crear archivo de subtítulos usando duracion_por_imagen
    srt_path = crear_archivo_srt(texto, duracion_audio, duracion_por_imagen)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("ffconcat version 1.0\n")
        duracion_acumulada = 0.0
        for i, img_path in enumerate(image_paths):
            duracion = (
                duracion_audio - duracion_acumulada
                if i == len(image_paths) - 1
                else duracion_por_imagen
            )
            f.write(f"file '{os.path.abspath(img_path)}'\n")
            f.write(f"duration {duracion:.6f}\n")
            duracion_acumulada += duracion
        list_file = f.name

    force_style = "Fontsize=15,Bold=1,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00222222&,Outline=1,Shadow=1,Alignment=2,MarginV=50"

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-fflags",
        "+genpts",
        "-vsync",
        "cfr",
        "-i",
        list_file,
        "-i",
        audio_path,
        "-vf",
        f"scale={width}:{height},subtitles={srt_path}:force_style={force_style}",
        "-af",
        "apad=pad_dur=0.1",
        "-c:v",
        "libx264",
        "-crf",
        "20",
        "-preset",
        "medium",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-pix_fmt",
        "yuv420p",
        output_path,
    ]

    subprocess.run(cmd, check=True)
    os.unlink(list_file)
    return output_path


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    audio_dir_abs = os.path.join(base_dir, AUDIO_DIR)

    with open("ideas_generadas.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            id_idea = row["ID"]
            idea_texto = row["Idea"]
            nicho = row["Nicho"]

            audio_path = os.path.join(audio_dir_abs, f"idea_{id_idea}_{nicho}.mp3")
            image_paths = generar_imagenes_dinamicamente(
                idea_texto, id_idea, audio_path, nicho
            )
            crear_video_ffmpeg(image_paths, audio_path, id_idea, nicho, idea_texto)

    torch.cuda.empty_cache()
    torch.cuda.ipc_collect()


if __name__ == "__main__":
    main()
