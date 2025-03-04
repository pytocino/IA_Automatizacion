import os
import csv
import re
import requests
import subprocess
import time
from typing import List, Optional
from pydub import AudioSegment
from utils import start_ollama, stop_ollama


class PromptGenerator:
    """Clase encargada de generar prompts de imágenes a partir de texto."""

    OUTPUT_FOLDER = "resources/prompts"
    CSV_HEADERS = ["ID", "Prompt"]
    TEXT_DIR = "resources/texto"
    AUDIO_DIR = "resources/audio"

    def __init__(self):
        os.makedirs(self.OUTPUT_FOLDER, exist_ok=True)

    def obtener_duracion_audio(self, nicho: str) -> float:
        audio_path = os.path.join(self.AUDIO_DIR, f"audio_{nicho}.mp3")
        if not os.path.exists(audio_path):
            return 40  # Valor por defecto (10 imágenes)

        audio = AudioSegment.from_mp3(audio_path)
        return len(audio) / 1000  # Convertir de milisegundos a segundos

    def crear_prompts(self, text: str, num_prompts: int) -> str:
        return f"""
        [INST]
        You are a professional prompt engineer specialized in image prompts. First, internally analyze the following text to identify distinct visual themes, scenarios, characters, and emotions. Draw inspiration from successful, engaging content practices.
        Then, generate {num_prompts} concise, clear, and self-contained prompts that each describe a distinct image concept. 
        Ensure that each prompt is visually appealing, original, and suitable for generating unique, cinematic images.
        
        IMPORTANT: Do not include any part of your internal reasoning in the final output. Output only the final image prompts, each separated by a line break, with no numbering, bullet points, or extra formatting.
        
        Text:
        {text}
        [INST]
        """

    def procesar_respuesta(self, respuesta: dict) -> str:
        content = respuesta.get("response", "").strip()
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
        content = "\n".join(
            line.strip() for line in content.split("\n") if line.strip()
        )
        return content

    def guardar_prompts_csv(self, prompts: List[str], archivo: str):
        with open(archivo, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(self.CSV_HEADERS)
            for i, prompt in enumerate(prompts, 1):
                prompt_limpio = re.sub(r"^\d+\.\s*", "", prompt)
                writer.writerow([i, prompt_limpio])

    def generar_prompts_deepseek(self, text: str, num_prompts: int) -> str:
        prompts = self.crear_prompts(text, num_prompts)
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "deepseek-r1:14b",
            "prompt": prompts,
            "stream": False,
        }

        # Iniciando Ollama
        start_ollama()
        time.sleep(8)

        try:
            response = requests.post(url, json=payload)
            data = response.json()
            return self.procesar_respuesta(data)
        finally:
            stop_ollama()

    def generate(self, nicho: str) -> Optional[str]:
        prompts_path = os.path.join(self.OUTPUT_FOLDER, f"prompts_{nicho}.csv")

        # Obtener duración del audio y calcular número de prompts
        duracion = self.obtener_duracion_audio(nicho)
        num_prompts = max(1, int(duracion // 4))  # Una imagen cada 4 segundos

        # Leer el texto del CSV
        csv_filename = os.path.join(self.TEXT_DIR, f"idea_{nicho}.csv")
        with open(csv_filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader)
            texto = row["Idea"]

        # Generamos la respuesta con el número calculado de prompts
        prompts_str = self.generar_prompts_deepseek(texto, num_prompts)
        prompts_list = [p.strip() for p in prompts_str.splitlines() if p.strip()]
        self.guardar_prompts_csv(prompts_list, prompts_path)

        return prompts_path
