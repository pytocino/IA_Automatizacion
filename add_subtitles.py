import os
import subprocess
import argparse
import csv


def obtener_duracion_audio(audio_path: str) -> float:
    """Obtiene la duración del archivo de audio en segundos"""
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


def crear_archivo_srt(texto: str, duracion_audio: float) -> str:
    """
    Crea un archivo SRT con el texto dividido según la duración de cada imagen
    """
    duracion_por_imagen = duracion_audio / 12

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

    srt_path = os.path.join("./subtitulos/subtitulos.srt")
    os.makedirs("subtitulos", exist_ok=True)

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    return srt_path


def add_subtitles(video_path: str) -> str:
    """Añade subtítulos a un video existente"""
    # Obtener ID y nicho del nombre del video
    filename = os.path.basename(video_path)

    # Leer el texto del CSV
    with open("ideas_generadas.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        texto = None
        for row in reader:
            texto = row["Idea"]

    if not texto:
        raise ValueError(f"No se encontró el texto para el video {filename}")

    # Obtener la duración del audio correspondiente
    audio_path = os.path.join("./audios/idea_1_sci-fi.mp3")
    duracion_audio = obtener_duracion_audio(audio_path)

    # Crear archivo de subtítulos
    srt_path = crear_archivo_srt(texto, duracion_audio)

    # Preparar ruta de salida
    output_path = os.path.join("./videos/subtitled_" + filename)

    # Estilo de los subtítulos
    force_style = "Fontsize=15,Bold=1,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00222222&,Outline=1,Shadow=1,Alignment=2,MarginV=50"

    # Comando FFmpeg para añadir subtítulos
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vf",
        f"subtitles={srt_path}:force_style='{force_style}'",
        "-c:a",
        "copy",
        output_path,
    ]

    subprocess.run(cmd, check=True)
    return output_path


if __name__ == "__main__":
    add_subtitles("./videos/video_1_sci-fi.mp4")
