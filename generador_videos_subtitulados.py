import os
import glob
import torch
import argparse
import subprocess
import tempfile
from PIL import Image
import soundfile as sf
import csv
import random  # Añadir al inicio del archivo con los otros imports
import math  # Añadir al inicio del archivo con los otros imports

# Directorios
IMAGE_DIR = "imagenes"
AUDIO_DIR = "audios"
VIDEO_DIR = "videos"


def obtener_duracion_audio(audio_path: str) -> float:
    """Obtiene la duración del archivo de audio"""
    data, samplerate = sf.read(audio_path)
    return len(data) / samplerate


def crear_archivo_srt(
    texto: str, duracion_audio: float, duracion_por_imagen: float, nicho: str
) -> str:
    """Crea un archivo SRT con bloques de 4-8 palabras cubriendo toda la duración"""
    palabras = texto.split()
    srt_content = ""
    palabras_restantes = palabras.copy()
    contador_bloques = 1
    tiempo_actual = 0

    # Calculamos un tiempo mínimo por bloque para evitar subtítulos muy cortos
    tiempo_minimo_bloque = 1.5  # 1.5 segundos mínimo por bloque

    # Calculamos el número total de bloques necesarios
    num_bloques_estimados = int(duracion_audio / tiempo_minimo_bloque)
    palabras_por_bloque = max(4, len(palabras) // num_bloques_estimados)

    while palabras_restantes:
        # Ajustamos el número de palabras según el tiempo restante
        palabras_restantes_total = len(palabras_restantes)
        tiempo_restante = duracion_audio - tiempo_actual

        if tiempo_restante <= tiempo_minimo_bloque:
            # Si queda poco tiempo, usamos todas las palabras restantes
            num_palabras = len(palabras_restantes)
        else:
            # Si no, usamos un número proporcional de palabras
            num_palabras = min(
                random.randint(4, 8),
                max(
                    4,
                    palabras_restantes_total
                    // max(1, int(tiempo_restante / tiempo_minimo_bloque)),
                ),
            )

        # Extraer las palabras para este bloque
        texto_bloque = " ".join(palabras_restantes[:num_palabras])
        palabras_restantes = palabras_restantes[num_palabras:]

        # Calcular duración proporcional
        if not palabras_restantes:
            # Para el último bloque, usar todo el tiempo restante
            fin_tiempo = duracion_audio
        else:
            # Para los demás bloques, calcular proporcionalmente
            duracion_bloque = max(
                tiempo_minimo_bloque, (num_palabras / len(palabras)) * duracion_audio
            )
            fin_tiempo = min(tiempo_actual + duracion_bloque, duracion_audio)

        # Convertir tiempos a formato SRT
        inicio_seg = int(tiempo_actual)
        inicio_ms = int((tiempo_actual - inicio_seg) * 1000)
        fin_seg = int(fin_tiempo)
        fin_ms = int((fin_tiempo - fin_seg) * 1000)

        inicio_str = f"{inicio_seg//3600:02d}:{(inicio_seg%3600)//60:02d}:{inicio_seg%60:02d},{inicio_ms:03d}"
        fin_str = f"{fin_seg//3600:02d}:{(fin_seg%3600)//60:02d}:{fin_seg%60:02d},{fin_ms:03d}"

        srt_content += (
            f"{contador_bloques}\n{inicio_str} --> {fin_str}\n{texto_bloque}\n\n"
        )

        tiempo_actual = fin_tiempo
        contador_bloques += 1

    srt_path = os.path.join("./subtitulos/", f"subtitulos_{nicho}.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    return srt_path


def crear_video(nicho: str, texto: str) -> str:
    """Crea un video usando las imágenes y audio existentes"""
    # Buscar imágenes y audio relacionados con el nicho
    imagenes = sorted(glob.glob(os.path.join(IMAGE_DIR, f"*{nicho}*.webp")))
    audio_path = glob.glob(os.path.join(AUDIO_DIR, f"*{nicho}*.mp3"))[0]

    if not imagenes or not audio_path:
        raise ValueError(f"No se encontraron recursos para el nicho: {nicho}")

    # Obtener dimensiones de la primera imagen
    with Image.open(imagenes[0]) as img:
        width, height = img.size

    # Calcular duraciones
    duracion_audio = obtener_duracion_audio(audio_path)
    # Añadimos margen adicional
    duracion_total = duracion_audio + 0.5
    duracion_por_imagen = duracion_total / len(imagenes)

    # Crear subtítulos nuevos
    srt_path = crear_archivo_srt(texto, duracion_audio, duracion_por_imagen, nicho)

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

    # Crear la ruta de salida correctamente
    output_path = os.path.join(VIDEO_DIR, f"video_backup_{nicho}.mp4")

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
        f"[0:v]fps=30,scale={width}:{height}[vid];[vid]subtitles={srt_path}:force_style='{force_style}'[v]",
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


def obtener_texto_csv(nicho: str) -> str:
    """Obtiene el texto del CSV basado en el nicho"""
    with open("ideas_generadas.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            return row["Idea"]


def main(nicho: str):
    texto = obtener_texto_csv(nicho)
    output_path = crear_video(nicho, texto)
    print(f"Video creado exitosamente: {output_path}")
    torch.cuda.empty_cache()
    torch.cuda.ipc_collect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--nicho", required=True, help="Nicho del video")
    args = parser.parse_args()
    main(args.nicho)
