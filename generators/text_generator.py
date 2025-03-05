import os
import csv
import re
import ollama
from typing import Optional
from utils import start_ollama, stop_ollama


class TextGenerator:
    """Clase encargada de generar textos/ideas para los videos."""

    OUTPUT_FOLDER = "resources/texto"
    CSV_HEADERS = ["ID", "Idea", "Nicho"]

    def __init__(self):
        os.makedirs(self.OUTPUT_FOLDER, exist_ok=True)

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
        start_ollama()

        try:
            # Crear modelo personalizado si no existe
            modelo = "storyteller"
            prompt = f"""
                Topic: {nicho}
                Time period: {era if era else "any relevant time period"}
                Location: {location if location else "appropriate geographical context"}
                Tone: {tone}
                Generate a micro-story following the system instructions.
            """

            response = ollama.generate(model=modelo, prompt=prompt, stream=False)

            texto_generado = response.get("response", "")
            return self.procesar_respuesta({"response": texto_generado})
        except Exception as e:
            print(f"Error al generar texto con Ollama: {e}")
            return None
        finally:
            stop_ollama()

    def generate(
        self, nicho: str, era: str = "", location: str = "", tone: str = "engaging"
    ) -> Optional[str]:
        nicho_archivo = nicho

        nicho_texto = nicho.replace("_", " ")

        csv_path = os.path.join(self.OUTPUT_FOLDER, f"idea_{nicho_archivo}.csv")
        idea = self.generar_ideas_deepseek(nicho_texto, era, location, tone)
        if idea:
            self.guardar_idea_csv(idea, nicho, csv_path)
            self.formatear_csv(csv_path)
            return csv_path
        return None
