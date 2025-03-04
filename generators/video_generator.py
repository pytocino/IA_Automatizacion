import os
import glob
import torch
import subprocess
import tempfile
import datetime
from PIL import Image


class VideoGenerator:
    """Clase encargada de generar videos a partir de imágenes, audio y subtítulos."""

    IMAGE_DIR = "resources/imagenes"
    AUDIO_DIR = "resources/audio"
    VIDEO_DIR = "resources/video"
    TEXT_DIR = "resources/texto"
    SUBTITULOS_DIR = "resources/subtitulos"

    def __init__(self):
        os.makedirs(self.VIDEO_DIR, exist_ok=True)

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

    def crear_video(
        self, nicho: str, duracion_audio: float, subtitulos_path: str, output_path: str
    ) -> str:
        audio_path = os.path.join(self.AUDIO_DIR, f"audio_{nicho}.mp3")
        imagenes = sorted(
            glob.glob(os.path.join(self.IMAGE_DIR, f"imagen_*_{nicho}.jpeg"))
        )

        with Image.open(imagenes[0]) as img:
            width, height = img.size

        duracion_total = duracion_audio + 0.5
        duracion_por_imagen = duracion_total / len(imagenes)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("ffconcat version 1.0\n")
            duracion_acumulada = 0.0
            for i, img_path in enumerate(imagenes):
                if i == len(imagenes) - 1:
                    duracion = duracion_total - duracion_acumulada
                else:
                    duracion = duracion_por_imagen

                f.write(f"file '{os.path.abspath(img_path)}'\n")
                f.write(f"duration {duracion:.6f}\n")
                duracion_acumulada += duracion

            list_file = f.name

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

    def generate(self, nicho: str, subtitulos_path: str) -> str:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        duracion_audio = self.obtener_duracion_audio(nicho)
        output_path = os.path.join(self.VIDEO_DIR, f"video_{nicho}_{timestamp}.mp4")

        self.crear_video(nicho, duracion_audio, subtitulos_path, output_path)
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()

        return output_path
