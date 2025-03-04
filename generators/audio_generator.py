import os
import csv
import gtts
from typing import Optional


class AudioGenerator:
    """Clase encargada de generar archivos de audio a partir de texto."""

    OUTPUT_DIR = "resources/audio"
    TEXT_DIR = "resources/texto"

    def __init__(self):
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)

    def generate(self, nicho: str) -> Optional[str]:
        """Genera un archivo de audio a partir de un archivo CSV."""
        csv_filename = os.path.join(self.TEXT_DIR, f"idea_{nicho}.csv")

        with open(csv_filename, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            row = next(reader)

            mp3_output_path = os.path.join(self.OUTPUT_DIR, f"audio_{nicho}.mp3")
            tts = gtts.gTTS(text=row["Idea"], slow=False)
            tts.save(mp3_output_path)

            return mp3_output_path
