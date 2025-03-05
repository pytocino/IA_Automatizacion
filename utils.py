import subprocess
import time
import logging
import os
import shutil


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


def stop_ollama(force=True):
    """Detiene el proceso de Ollama"""
    try:
        # Primero intentamos un cierre normal
        subprocess.run(
            ["taskkill", "/IM", "ollama.exe"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        if force:
            # Si es necesario, forzamos el cierre
            subprocess.run(
                ["taskkill", "/F", "/IM", "ollama.exe"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
    except Exception as e:
        logging.error(f"Error al detener Ollama: {str(e)}")


def borrar_recursos_generados():
    """
    Borra todos los archivos generados en las carpetas de recursos.
    Mantiene la estructura de directorios intacta.
    """
    recursos_path = "resources"

    # Lista de subcarpetas a limpiar dentro de resources
    subcarpetas = ["texto", "audio", "prompts", "imagenes", "video", "subtitulos"]

    try:
        for subcarpeta in subcarpetas:
            ruta_completa = os.path.join(recursos_path, subcarpeta)

            # Verificar si existe la carpeta antes de intentar limpiarla
            if os.path.exists(ruta_completa):
                # Opción 1: Borrar todos los archivos pero mantener la carpeta
                for archivo in os.listdir(ruta_completa):
                    ruta_archivo = os.path.join(ruta_completa, archivo)
                    try:
                        if os.path.isfile(ruta_archivo):
                            os.remove(ruta_archivo)
                            logging.info(f"Archivo eliminado: {ruta_archivo}")
                        elif os.path.isdir(ruta_archivo):
                            shutil.rmtree(ruta_archivo)
                            logging.info(f"Carpeta eliminada: {ruta_archivo}")
                    except Exception as e:
                        logging.error(f"Error al eliminar {ruta_archivo}: {str(e)}")

                logging.info(f"Carpeta limpiada: {ruta_completa}")
            else:
                os.makedirs(ruta_completa, exist_ok=True)
                logging.info(f"Carpeta creada: {ruta_completa}")

        logging.info("Todos los recursos generados han sido eliminados")
        return True
    except Exception as e:
        logging.error(f"Error al borrar recursos generados: {str(e)}")
        return False
