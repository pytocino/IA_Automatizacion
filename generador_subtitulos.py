import random
import os
import argparse
import csv
import subprocess

SUBTITULOS_DIR = "resources/subtitulos"
TEXT_DIR = "resources/texto"
AUDIO_DIR = "resources/audio"


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


def crear_archivo_srt(texto: str, duracion_audio: float, nicho: str) -> str:
    """Crea un archivo SRT con bloques de 4-8 palabras cubriendo toda la duración"""
    palabras = texto.split()
    srt_content = ""
    palabras_restantes = palabras.copy()
    contador_bloques = 1
    tiempo_actual = 0
    tiempo_minimo_bloque = 1.5

    num_bloques_estimados = int(duracion_audio / tiempo_minimo_bloque)
    palabras_por_bloque = max(4, len(palabras) // num_bloques_estimados)

    while palabras_restantes:
        palabras_restantes_total = len(palabras_restantes)
        tiempo_restante = duracion_audio - tiempo_actual

        if tiempo_restante <= tiempo_minimo_bloque:
            num_palabras = len(palabras_restantes)
        else:
            num_palabras = min(
                random.randint(4, 8),
                max(
                    4,
                    palabras_restantes_total
                    // max(1, int(tiempo_restante / tiempo_minimo_bloque)),
                ),
            )

        texto_bloque = " ".join(palabras_restantes[:num_palabras])
        palabras_restantes = palabras_restantes[num_palabras:]

        if not palabras_restantes:
            fin_tiempo = duracion_audio
        else:
            duracion_bloque = max(
                tiempo_minimo_bloque, (num_palabras / len(palabras)) * duracion_audio
            )
            fin_tiempo = min(tiempo_actual + duracion_bloque, duracion_audio)

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
