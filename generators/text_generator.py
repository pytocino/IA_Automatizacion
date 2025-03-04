import os
import csv
import re
import requests
import subprocess
import time
from typing import Optional, List
from utils import start_ollama, stop_ollama


class TextGenerator:
    """Clase encargada de generar textos/ideas para los videos."""

    OUTPUT_FOLDER = "resources/texto"
    CSV_HEADERS = ["ID", "Idea", "Nicho"]

    def __init__(self):
        os.makedirs(self.OUTPUT_FOLDER, exist_ok=True)

    def crear_prompt(
        self, nicho: str, era: str = "", location: str = "", tone: str = "engaging"
    ) -> str:
        return f"""
            [INST]
            You are a professional storyteller and narrative designer specialized in {nicho} stories with a factual or historical twist.
            
            First, internally analyze:
            1. The core historical or factual elements of {nicho} that would surprise most viewers
            2. Visual imagery that could be captured in short-form video format
            3. Emotional hooks that create immediate interest in {nicho}
            4. How to incorporate {era if era else "any relevant time period"} and {location if location else "appropriate geographical context"}
            5. Ways to maintain a {tone} tone while being educational
            
            Then, generate one unique micro-story following these guidelines:
            - Begin with a hook starting with "Did you know...?" to introduce a surprising or intriguing fact
            - Length: 40-50 words maximum.
            - Focus on creating cinematic, visual moments that viewers can easily imagine
            - Include one specific detail (date, name, number) for authenticity
            - Ensure historical accuracy while maintaining narrative intrigue
            - Avoid clichés and overly familiar historical references
            
            IMPORTANT: Output only the final micro-story text, without any explanation, reasoning, or title.
            [/INST]
        """

    def procesar_respuesta(self, respuesta: dict) -> str:
        content = respuesta.get("response", "").strip()
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
        content = re.sub(r"\n\s*\n", "\n", content.strip())
        return content.strip()

    def guardar_idea_csv(self, idea: str, nicho: str, archivo: str):
        with open(archivo, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.CSV_HEADERS)
            writer.writerow([1, idea, nicho])

    def formatear_csv(self, archivo: str):
        with open(archivo, "r", encoding="utf-8") as f:
            contenido = f.read()

        dentro_comillas = False
        nuevo_contenido = []
        for char in contenido:
            if char == '"':
                dentro_comillas = not dentro_comillas
            if dentro_comillas and char == "\n":
                nuevo_contenido.append(" ")
            else:
                nuevo_contenido.append(char)

        with open(archivo, "w", encoding="utf-8", newline="") as f:
            f.write("".join(nuevo_contenido))

    def generar_ideas_deepseek(
        self, nicho: str, era: str, location: str, tone: str
    ) -> Optional[str]:
        prompt = self.crear_prompt(nicho, era, location, tone)
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "deepseek-r1:14b",
            "prompt": prompt,
            "stream": False,
        }

        # Iniciando Ollama
        start_ollama()
        time.sleep(8)

        try:
            response = requests.post(url, json=payload)
            data = response.json()
            texto_generado = data.get("response", "")
            return self.procesar_respuesta({"response": texto_generado})
        finally:
            stop_ollama()

    def generate(
        self, nicho: str, era: str = "", location: str = "", tone: str = "engaging"
    ) -> Optional[str]:
        # Preservar el nicho con guiones bajos para nombres de archivo
        nicho_archivo = nicho

        # Convertir guiones bajos a espacios para el prompt y la generación de texto
        nicho_texto = nicho.replace("_", " ")

        csv_path = os.path.join(self.OUTPUT_FOLDER, f"idea_{nicho_archivo}.csv")
        idea = self.generar_ideas_deepseek(nicho_texto, era, location, tone)
        if idea:
            self.guardar_idea_csv(idea, nicho, csv_path)
            self.formatear_csv(csv_path)
            return csv_path
        return None
