import subprocess
import time
import logging


def start_ollama():
    """Inicia el servicio de Ollama si no está en ejecución"""
    try:
        # Verificar si Ollama ya está en ejecución
        subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq ollama.exe"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

        # Intentar iniciar Ollama en segundo plano
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        # Esperar a que el servicio esté disponible
        time.sleep(2)
    except Exception as e:
        logging.error(f"Error al iniciar Ollama: {str(e)}")


def stop_ollama():
    """Detiene el proceso de Ollama"""
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "ollama.exe"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except subprocess.CalledProcessError:
        logging.warning("No se encontró proceso de Ollama para detener")
    except Exception as e:
        logging.error(f"Error al detener Ollama: {str(e)}")
