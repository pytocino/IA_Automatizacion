import os
import glob
import torch
import argparse
import subprocess
import tempfile
from PIL import Image
import csv
import datetime  # Añadido para manejar fecha y hora


# Directorios
IMAGE_DIR = "resources/imagenes"
AUDIO_DIR = "resources/audio"
VIDEO_DIR = "resources/video"
TEXT_DIR = "resources/texto"
SUBTITULOS_DIR = "resources/subtitulos/"


def obtener_texto_csv(nicho: str) -> str:
    """Obtiene el texto del CSV basado en el nicho"""
    csv_filename = os.path.join(TEXT_DIR, f"idea_{nicho}.csv")

    with open(csv_filename, mode="r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        row = next(reader)
        return row["Idea"]


def obtener_duracion_audio(nicho: str) -> float:
    """Obtiene la duración de un archivo de audio usando ffprobe."""
    audio_path = os.path.join(AUDIO_DIR, f"audio_{nicho}.mp3")
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
    return float(subprocess.check_output(comando).decode().strip())


def crear_video(
    nicho: str,
    duracion_audio: float,
    subtitulos_path: str,
    output_path: str,
) -> str:
    """Crea un video usando las imágenes y audio existentes"""
    audio_path = os.path.join(AUDIO_DIR, f"audio_{nicho}.mp3")
    imagenes = sorted(glob.glob(os.path.join(IMAGE_DIR, f"imagen_*_{nicho}.jpeg")))

    with Image.open(imagenes[0]) as img:
        width, height = img.size

    duracion_total = duracion_audio + 0.5
    duracion_por_imagen = duracion_total / len(imagenes)

    # Crear archivo de lista temporal para FFmpeg
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("ffconcat version 1.0\n")
        duracion_acumulada = 0.0
        for i, img_path in enumerate(imagenes):
            if i == len(imagenes) - 1:
                # La última imagen dura hasta el final del audio más el margen
                duracion = duracion_total - duracion_acumulada
            else:
                duracion = duracion_por_imagen

            # Escribimos cada imagen con su duración
            f.write(f"file '{os.path.abspath(img_path)}'\n")
            f.write(f"duration {duracion:.6f}\n")
            duracion_acumulada += duracion

        # Ya no añadimos la última imagen extra
        list_file = f.name

    # Modificar el force_style para escapar caracteres especiales
    force_style = (
        "Fontsize=15,"
        "Bold=1,"
        "PrimaryColour=&HFFFFFF,"
        "OutlineColour=&H222222,"
        "Outline=1,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=50"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        list_file,
        "-i",
        audio_path,
        "-filter_complex",
        f"[0:v]fps=30,scale={width}:{height}[vid];[vid]subtitles={subtitulos_path}:force_style='{force_style}'[v]",
        "-map",
        "[v]",
        "-map",
        "1:a",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-shortest",
        "-avoid_negative_ts",
        "make_zero",
        "-pix_fmt",
        "yuv420p",
        output_path,
    ]

    subprocess.run(cmd, check=True)
    os.unlink(list_file)
    return output_path


def main(nicho: str):
    os.makedirs(VIDEO_DIR, exist_ok=True)

    # Eliminar espacios del nicho
    nicho_sin_espacios = nicho.replace(" ", "_")

    # Obtener fecha y hora actual en formato YYYYMMDD_HHMMSS
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    texto = obtener_texto_csv(nicho)
    duracion_audio = obtener_duracion_audio(nicho)
    subtitulos_path = os.path.join(SUBTITULOS_DIR, f"subtitulos_{nicho}.srt")

    # Modificar el nombre del archivo de salida
    output_path = os.path.join(VIDEO_DIR, f"video_{nicho_sin_espacios}_{timestamp}.mp4")

    crear_video(nicho, duracion_audio, subtitulos_path, output_path)
    torch.cuda.empty_cache()
    torch.cuda.ipc_collect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--nicho", required=True, help="Nicho del video")
    args = parser.parse_args()
    main(args.nicho)
