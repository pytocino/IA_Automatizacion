import os
import csv
import subprocess
from typing import Optional


class SubtitleGenerator:
    """Clase encargada de generar subtítulos para los videos."""

    SUBTITULOS_DIR = "resources/subtitulos/"
    TEXT_DIR = "resources/texto"
    AUDIO_DIR = "resources/audio"
    PROMPTS_DIR = "resources/prompts"

    def __init__(self):
        os.makedirs(self.SUBTITULOS_DIR, exist_ok=True)

    def obtener_texto_csv(self, nicho: str) -> str:
        csv_filename = os.path.join(self.TEXT_DIR, f"idea_{nicho}.csv")
        with open(csv_filename, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            row = next(reader)
            return row["Idea"]

    def obtener_duracion_audio(self, nicho: str) -> float:
        audio_path = os.path.join(self.AUDIO_DIR, f"audio_{nicho}.mp3")
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

    def obtener_numero_prompts(self, nicho: str) -> int:
        prompts_path = os.path.join(self.PROMPTS_DIR, f"prompts_{nicho}.csv")
        with open(prompts_path, mode="r", newline="", encoding="utf-8") as csvfile:
            return sum(1 for _ in csv.DictReader(csvfile))

    def crear_archivo_srt(self, texto: str, duracion_audio: float, nicho: str) -> str:
        palabras = texto.split()
        srt_content = ""
        num_imagenes = self.obtener_numero_prompts(nicho)

        palabras_por_bloque = len(palabras) // num_imagenes
        palabras_extra = len(palabras) % num_imagenes

        tiempo_por_bloque = duracion_audio / num_imagenes
        tiempo_actual = 0

        for i in range(num_imagenes):
            num_palabras = palabras_por_bloque + (1 if i < palabras_extra else 0)
            inicio = i * palabras_por_bloque + min(i, palabras_extra)
            fin = inicio + num_palabras
            texto_bloque = " ".join(palabras[inicio:fin])

            fin_tiempo = min((i + 1) * tiempo_por_bloque, duracion_audio)

            inicio_seg = int(tiempo_actual)
            inicio_ms = int((tiempo_actual - inicio_seg) * 1000)
            fin_seg = int(fin_tiempo)
            fin_ms = int((fin_tiempo - fin_seg) * 1000)

            inicio_str = f"{inicio_seg//3600:02d}:{(inicio_seg%3600)//60:02d}:{inicio_seg%60:02d},{inicio_ms:03d}"
            fin_str = f"{fin_seg//3600:02d}:{(fin_seg%3600)//60:02d}:{fin_seg%60:02d},{fin_ms:03d}"

            srt_content += f"{i + 1}\n{inicio_str} --> {fin_str}\n{texto_bloque}\n\n"

            tiempo_actual = fin_tiempo

        srt_path = os.path.join(self.SUBTITULOS_DIR, f"subtitulos_{nicho}.srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)

        return srt_path

    def generate(self, nicho: str) -> Optional[str]:
        """Genera un archivo de subtítulos para un nicho específico."""
        try:
            texto = self.obtener_texto_csv(nicho)
            duracion_audio = self.obtener_duracion_audio(nicho)
            srt_path = self.crear_archivo_srt(texto, duracion_audio, nicho)
            return srt_path
        except Exception:
            return None
