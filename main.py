import os
import asyncio
import multiprocessing
import time
from multiprocessing import Process
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
import sys
from utils import borrar_recursos_generados, stop_ollama

# Diccionario para almacenar procesos activos
active_processes = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    # Create keyboard buttons
    keyboard = [
        [KeyboardButton("/run"), KeyboardButton("/last_video")],
        [KeyboardButton("/clean"), KeyboardButton("/cancel")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_html(
        f"Hola tocino! Selecciona una de las siguientes opciones:",
        reply_markup=reply_markup,
    )


async def run_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ejecuta la automatización directamente con configuración aleatoria"""
    chat_id = update.effective_chat.id

    # Verificar si ya hay un proceso activo para este usuario
    user_processes = [
        pid for pid in active_processes.keys() if pid.startswith(f"{chat_id}_")
    ]
    if user_processes:
        await update.message.reply_text(
            "Ya tienes un proceso activo. Usa /cancel para detenerlo antes de iniciar uno nuevo."
        )
        return

    await update.message.reply_text("Iniciando proceso de automatización...")

    # Inicia la tarea en un proceso separado
    process_id = f"{chat_id}_random"
    result_queue = multiprocessing.Queue()

    process = Process(target=run_automation_in_process, args=(process_id, result_queue))
    process.daemon = (
        True  # Importante: esto asegura que el proceso hijo termine si el padre termina
    )
    process.start()

    # Registramos el trabajo en proceso
    active_processes[process_id] = {
        "process": process,
        "start_time": time.time(),
        "result_queue": result_queue,
    }

    # Iniciar la tarea de monitoreo del proceso
    context.application.create_task(monitor_process(chat_id, process_id))


def run_automation_in_process(process_id, result_queue):
    """Esta función se ejecuta en un proceso separado"""
    try:
        from automation import VideoAutomation

        # Ejecutamos la automatización
        automation = VideoAutomation()
        result = automation.generate_video()  # Nicho aleatorio

        # Enviamos el resultado al proceso principal
        result_queue.put(result)

    except Exception as e:
        result_queue.put({"error": str(e)})
    finally:
        # Asegurar que Ollama está detenido en este proceso
        stop_ollama()


async def monitor_process(chat_id, process_id):
    """Monitorea el proceso de automatización y notifica cuando termina"""
    if process_id not in active_processes:
        return

    process_info = active_processes[process_id]
    process = process_info["process"]
    result_queue = process_info["result_queue"]

    # Esperar a que el proceso termine o revisar periódicamente
    while process.is_alive():
        await asyncio.sleep(2)  # Revisar cada 2 segundos

    # Obtener el resultado (si está disponible)
    result = None
    if not result_queue.empty():
        result = result_queue.get(timeout=1)

    # Notificar al usuario
    if result:
        if "error" in result:
            await application.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Error en la automatización: {result['error']}",
            )
        else:
            await application.bot.send_message(
                chat_id=chat_id,
                text=f"✅ Automatización completada exitosamente\n"
                f"Nicho: {result['nicho']}\n"
                f"Video generado en: {result['video_path']}",
            )
    else:
        await application.bot.send_message(
            chat_id=chat_id, text="❌ Proceso terminado sin resultados disponibles"
        )

    # Eliminar el proceso de los activos
    if process_id in active_processes:
        # Limpiar recursos
        process.terminate() if process.is_alive() else None
        del active_processes[process_id]


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancela cualquier proceso activo del usuario"""
    chat_id = update.effective_chat.id
    user_processes = [
        pid for pid in active_processes.keys() if pid.startswith(f"{chat_id}_")
    ]

    if not user_processes:
        await update.message.reply_text("No hay procesos activos para cancelar.")
        return

    # Cancela todos los procesos del usuario
    for process_id in user_processes:
        process_info = active_processes[process_id]
        if "process" in process_info and process_info["process"].is_alive():
            process_info["process"].terminate()
        del active_processes[process_id]

    await update.message.reply_text("Proceso(s) cancelado(s).")


async def clean_resources_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Borra todos los recursos generados en las carpetas"""
    # Verificar si hay procesos activos
    chat_id = update.effective_chat.id
    user_processes = [
        pid for pid in active_processes.keys() if pid.startswith(f"{chat_id}_")
    ]

    if user_processes:
        await update.message.reply_text(
            "No se pueden limpiar los recursos mientras hay procesos activos. "
            "Usa /cancel para detener los procesos primero."
        )
        return

    await update.message.reply_text("Limpiando recursos generados...")

    # Ejecutamos la limpieza en segundo plano para no bloquear
    context.application.create_task(clean_resources_task(chat_id))


async def clean_resources_task(chat_id):
    try:
        success = borrar_recursos_generados()
        if success:
            await application.bot.send_message(
                chat_id=chat_id,
                text="✅ Todos los recursos generados han sido eliminados correctamente.",
            )
        else:
            await application.bot.send_message(
                chat_id=chat_id,
                text="❌ Hubo un error al eliminar los recursos generados.",
            )
    except Exception as e:
        await application.bot.send_message(
            chat_id=chat_id, text=f"❌ Error inesperado durante la limpieza: {str(e)}"
        )


async def last_video_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Envía el último video generado en la carpeta resources/video"""
    video_dir = "resources/video"

    if not os.path.exists(video_dir):
        await update.message.reply_text("La carpeta de videos no existe.")
        return

    # Obtener todos los archivos de video en la carpeta
    video_files = [
        os.path.join(video_dir, f)
        for f in os.listdir(video_dir)
        if os.path.isfile(os.path.join(video_dir, f))
        and f.lower().endswith((".mp4", ".avi", ".mov", ".wmv", ".mkv"))
    ]

    if not video_files:
        await update.message.reply_text("No hay videos disponibles.")
        return

    # Encontrar el archivo de video más reciente
    last_video = max(video_files, key=os.path.getmtime)

    try:
        # Enviar el mensaje de que estamos procesando
        await update.message.reply_text("Enviando el último video generado...")

        # Enviar el video
        with open(last_video, "rb") as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=f"Último video generado: {os.path.basename(last_video)}",
                supports_streaming=True,
            )
    except Exception as e:
        await update.message.reply_text(f"Error al enviar el video: {str(e)}")


def main() -> None:
    os.makedirs("log", exist_ok=True)
    load_dotenv()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        sys.exit(1)

    global application
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("run", run_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("last_video", last_video_command))
    application.add_handler(CommandHandler("clean", clean_resources_command))

    application.run_polling()


if __name__ == "__main__":
    main()
