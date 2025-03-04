import os
import json
import random
from typing import Optional, Dict, Any, Tuple, List

from generators.text_generator import TextGenerator
from generators.audio_generator import AudioGenerator
from generators.prompt_generator import PromptGenerator
from generators.image_generator import ImageGenerator
from generators.subtitle_generator import SubtitleGenerator
from generators.video_generator import VideoGenerator


class ResourceManager:
    """Gestiona los directorios y recursos necesarios para el sistema."""

    @staticmethod
    def ensure_directories() -> None:
        """Crea las estructuras de directorios necesarias."""
        directories = [
            "resources/texto",
            "resources/audio",
            "resources/prompts",
            "resources/imagenes",
            "resources/subtitulos",
            "resources/video",
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)


class ConfigManager:
    """Gestiona la configuración del sistema."""

    def __init__(self, config_path: str = "config.json"):
        """
        Inicializa el gestor de configuración.

        Args:
            config_path: Ruta al archivo de configuración
        """
        self.config_path = config_path

    def load_config(self) -> Dict[str, Any]:
        """Carga la configuración desde el archivo JSON"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"nichos": []}

    def select_random_config(self) -> Tuple[str, str, str, str, Optional[int]]:
        """
        Selecciona aleatoriamente un nicho y sus parámetros.

        Returns:
            Tuple con (nicho, era, ubicación, tono, semilla)
        """
        config = self.load_config()

        if not config["nichos"]:
            return "Ancient Technology", "", "", "engaging", None

        # Seleccionar un nicho aleatorio
        nicho_config = random.choice(config["nichos"])

        nicho = nicho_config["name"]
        era = random.choice(nicho_config["eras"]) if nicho_config.get("eras") else ""
        location = (
            random.choice(nicho_config["locations"])
            if nicho_config.get("locations")
            else ""
        )
        tone = (
            random.choice(nicho_config["tones"])
            if nicho_config.get("tones")
            else "engaging"
        )
        seed = random.randint(1, 1000000)  # Semilla aleatoria

        return nicho, era, location, tone, seed

    def get_nicho_config(self, nicho_name: str) -> Dict[str, Any]:
        """
        Obtiene la configuración para un nicho específico.

        Args:
            nicho_name: Nombre del nicho a buscar

        Returns:
            Diccionario con la configuración del nicho o None si no existe
        """
        config = self.load_config()

        for nicho in config.get("nichos", []):
            if nicho["name"] == nicho_name:
                return nicho

        return None


class VideoGenerationPipeline:
    """Clase que maneja el pipeline completo de generación de videos."""

    def __init__(self):
        self.text_generator = TextGenerator()
        self.audio_generator = AudioGenerator()
        self.prompt_generator = PromptGenerator()
        self.image_generator = ImageGenerator()
        self.subtitle_generator = SubtitleGenerator()
        self.video_generator = VideoGenerator()

    def generate(
        self,
        nicho: str,
        era: str = "",
        location: str = "",
        tone: str = "engaging",
        seed: Optional[int] = None,
    ) -> str:
        """
        Ejecuta el pipeline completo de generación de video.

        Args:
            nicho: Tema o nicho del video
            era: Período histórico
            location: Ubicación geográfica
            tone: Tono emocional de la narrativa
            seed: Semilla para generación de imágenes

        Returns:
            str: Ruta al video generado
        """
        nicho_procesado = nicho.replace(" ", "_")

        self.text_generator.generate(nicho_procesado, era, location, tone)
        self.audio_generator.generate(nicho_procesado)
        self.prompt_generator.generate(nicho_procesado)
        self.image_generator.generate(nicho_procesado, seed)
        subtitles_path = self.subtitle_generator.generate(nicho_procesado)
        video_path = self.video_generator.generate(nicho_procesado, subtitles_path)

        return video_path


class VideoAutomation:
    """
    Clase principal que coordina todo el proceso de automatización de videos.
    Esta clase es utilizada por telegram_bot.py.
    """

    def __init__(self, config_path: str = "config.json"):
        """
        Inicializa la automatización de videos.

        Args:
            config_path: Ruta al archivo de configuración
        """
        self.resource_manager = ResourceManager()
        self.config_manager = ConfigManager(config_path)
        self.pipeline = VideoGenerationPipeline()

        # Asegurar que las carpetas necesarias existan
        self.resource_manager.ensure_directories()

    def generate_video(self, nicho: Optional[str] = None) -> Dict[str, Any]:
        """
        Genera un video basado en el nicho especificado o aleatorio.

        Args:
            nicho: Nombre del nicho específico (opcional)

        Returns:
            Dict con información del video generado, incluyendo video_path
        """
        if nicho:
            # Usar el nicho específico
            nicho_config = self.config_manager.get_nicho_config(nicho)
            if not nicho_config:
                return {
                    "error": f"No se encontró el nicho: {nicho}",
                    "video_path": None,
                }

            # Seleccionar parámetros aleatorios del nicho específico
            era = (
                random.choice(nicho_config.get("eras", [""]))
                if nicho_config.get("eras")
                else ""
            )
            location = (
                random.choice(nicho_config.get("locations", [""]))
                if nicho_config.get("locations")
                else ""
            )
            tone = (
                random.choice(nicho_config.get("tones", ["engaging"]))
                if nicho_config.get("tones")
                else "engaging"
            )
            seed = random.randint(1, 1000000)
        else:
            # Seleccionar nicho y parámetros aleatorios
            nicho, era, location, tone, seed = (
                self.config_manager.select_random_config()
            )

        # Generar el video
        try:
            video_path = self.pipeline.generate(
                nicho=nicho, era=era, location=location, tone=tone, seed=seed
            )

            return {
                "video_path": video_path,
                "nicho": nicho,
                "era": era,
                "location": location,
                "tone": tone,
                "seed": seed,
            }
        except Exception as e:
            return {"error": str(e), "video_path": None}


def main():
    """Función principal para ejecutar el proceso desde línea de comandos."""
    automation = VideoAutomation()
    result = automation.generate_video()

    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Video generado exitosamente: {result['video_path']}")
        print(f"Nicho: {result['nicho']}")


if __name__ == "__main__":
    main()
