import random
import os
import argparse
import csv
import subprocess

SUBTITULOS_DIR = "resources/subtitulos"
TEXT_DIR = "resources/texto"
AUDIO_DIR = "resources/audio"
PROMPTS_DIR = "resources/prompts"


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


def obtener_numero_prompts(nicho: str) -> int:
    """Obtiene el número de prompts del archivo CSV"""
    prompts_path = os.path.join(PROMPTS_DIR, f"prompts_{nicho}.csv")
    with open(prompts_path, mode="r", newline="", encoding="utf-8") as csvfile:
        return sum(1 for _ in csv.DictReader(csvfile))


def crear_archivo_srt(texto: str, duracion_audio: float, nicho: str) -> str:
    """Crea un archivo SRT con bloques que coinciden con el número de imágenes"""
    palabras = texto.split()
    srt_content = ""
    num_imagenes = obtener_numero_prompts(nicho)

    # Distribuir palabras equitativamente entre bloques
    palabras_por_bloque = len(palabras) // num_imagenes
    palabras_extra = len(palabras) % num_imagenes

    tiempo_por_bloque = duracion_audio / num_imagenes
    tiempo_actual = 0

    for i in range(num_imagenes):
        # Calcular palabras para este bloque
        num_palabras = palabras_por_bloque + (1 if i < palabras_extra else 0)
        inicio = i * palabras_por_bloque + min(i, palabras_extra)
        fin = inicio + num_palabras
        texto_bloque = " ".join(palabras[inicio:fin])

        # Calcular tiempos
        fin_tiempo = min((i + 1) * tiempo_por_bloque, duracion_audio)

        inicio_seg = int(tiempo_actual)
        inicio_ms = int((tiempo_actual - inicio_seg) * 1000)
        fin_seg = int(fin_tiempo)
        fin_ms = int((fin_tiempo - fin_seg) * 1000)

        inicio_str = f"{inicio_seg//3600:02d}:{(inicio_seg%3600)//60:02d}:{inicio_seg%60:02d},{inicio_ms:03d}"
        fin_str = f"{fin_seg//3600:02d}:{(fin_seg%3600)//60:02d}:{fin_seg%60:02d},{fin_ms:03d}"

        srt_content += f"{i + 1}\n{inicio_str} --> {fin_str}\n{texto_bloque}\n\n"

        tiempo_actual = fin_tiempo

    srt_path = os.path.join(SUBTITULOS_DIR, f"subtitulos_{nicho}.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    return srt_path


def main(nicho: str):
    os.makedirs(SUBTITULOS_DIR, exist_ok=True)

    texto = obtener_texto_csv(nicho)
    duracion_audio = obtener_duracion_audio(nicho)
    crear_archivo_srt(texto, duracion_audio, nicho)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--nicho", required=True, help="Nicho del video")
    args = parser.parse_args()
    main(args.nicho)
