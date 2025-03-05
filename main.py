import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
import sys
from utils import borrar_recursos_generados

# Diccionario para almacenar procesos activos
active_processes = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        f"Hola, {user.mention_html()}! Soy el bot de automatización de contenido.\n"
        "Usa /run para iniciar la generación de contenido y /cancel para detener procesos.\n"
        "Usa /last_video para obtener el último video generado.\n"
        "Usa /clean para borrar todos los recursos generados."
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

    # Inicia la tarea en segundo plano
    context.application.create_task(execute_automation(chat_id))


async def execute_automation(chat_id):
    from automation import VideoAutomation
    import gc

    process_id = f"{chat_id}_random"
    automation = None

    # Registramos el trabajo en proceso
    active_processes[process_id] = {
        "start_time": asyncio.get_event_loop().time(),
    }

    try:
        # Ejecutamos la automatización con configuración aleatoria
        automation = VideoAutomation()
        result = automation.generate_video()  # Nicho aleatorio

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
    except Exception as e:
        await application.bot.send_message(
            chat_id=chat_id, text=f"❌ Error inesperado: {str(e)}"
        )
    finally:
        # Limpiamos el proceso de la lista de activos
        if process_id in active_processes:
            del active_processes[process_id]

        # Liberar recursos explícitamente
        if automation:
            if hasattr(automation.pipeline, "image_generator"):
                # Liberar recursos de la GPU
                del automation.pipeline.image_generator

            # Liberar el resto de generadores
            for attr in [
                "text_generator",
                "audio_generator",
                "prompt_generator",
                "subtitle_generator",
                "video_generator",
            ]:
                if hasattr(automation.pipeline, attr):
                    setattr(automation.pipeline, attr, None)

            # Eliminar el objeto completo
            del automation.pipeline
            del automation

        # Asegurarse que Ollama está detenido
        from utils import stop_ollama

        stop_ollama()

        # Forzar recolección de basura
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

        gc.collect()


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
