import os
import json
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import subprocess
import sys

active_processes = {}


def load_config(config_path="config.json"):
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)
    return {"nichos": []}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        f"Hola, {user.mention_html()}! Soy el bot de automatización de contenido.\n"
        "Usa /help para ver los comandos disponibles."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "Comandos disponibles:\n"
        "/start - Iniciar el bot\n"
        "/help - Mostrar este mensaje de ayuda\n"
        "/run - Ejecutar la automatización\n"
        "/status - Ver el estado de las tareas en ejecución\n"
        "/cancel - Cancelar una tarea en ejecución\n"
        "/list_nichos - Listar los nichos disponibles\n"
    )
    await update.message.reply_text(help_text)


async def list_nichos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config = load_config()
    nichos = config.get("nichos", [])

    if not nichos:
        await update.message.reply_text("No hay nichos configurados.")
        return

    nicho_text = "Nichos disponibles:\n\n"
    for i, nicho in enumerate(nichos, 1):
        nicho_text += f"{i}. {nicho['name']}\n"

    await update.message.reply_text(nicho_text)


async def run_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config = load_config()
    nichos = config.get("nichos", [])

    if not nichos:
        await update.message.reply_text("No hay nichos configurados.")
        return

    keyboard = []
    for nicho in nichos:
        keyboard.append(
            [InlineKeyboardButton(nicho["name"], callback_data=f"run_{nicho['name']}")]
        )
    keyboard.append([InlineKeyboardButton("Aleatorio", callback_data="run_random")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Selecciona un nicho para ejecutar:", reply_markup=reply_markup
    )


async def execute_automation(chat_id, nicho_name=None):
    cmd = ["py", "main.py"]

    if nicho_name and nicho_name != "random":
        config = load_config()
        nichos = config.get("nichos", [])

        selected_nicho = None
        for nicho in nichos:
            if nicho["name"] == nicho_name:
                selected_nicho = nicho
                break

        if not selected_nicho:
            await application.bot.send_message(
                chat_id=chat_id,
                text=f"Error: No se encontró el nicho '{nicho_name}'",
            )
            return

        temp_config = {"nichos": [selected_nicho]}
        with open("temp_config.json", "w", encoding="utf-8") as f:
            json.dump(temp_config, f, ensure_ascii=False, indent=2)
        cmd.extend(["--config", "temp_config.json"])

    await application.bot.send_message(
        chat_id=chat_id, text="Iniciando proceso de automatización..."
    )

    process_id = f"{chat_id}_{nicho_name or 'random'}"

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )

    active_processes[process_id] = {
        "process": process,
        "cmd": cmd,
        "nicho": nicho_name or "random",
        "start_time": asyncio.get_event_loop().time(),
    }

    await application.bot.send_message(
        chat_id=chat_id,
        text=f"Proceso iniciado para {nicho_name or 'nicho aleatorio'}. ID: {process_id}",
    )

    # Monitoreamos la salida del proceso
    while True:
        line = await process.stdout.readline()
        if not line:
            break
        # Procesar la salida si es necesario

    await process.wait()

    if process.returncode == 0:
        await application.bot.send_message(
            chat_id=chat_id,
            text=f"✅ Automatización completada exitosamente para {nicho_name or 'nicho aleatorio'}",
        )
    else:
        stderr_data = await process.stderr.read()
        error_message = (
            stderr_data.decode("utf-8") if stderr_data else "Error desconocido"
        )
        await application.bot.send_message(
            chat_id=chat_id, text=f"❌ Error en la automatización: {error_message}"
        )

    if process_id in active_processes:
        del active_processes[process_id]

    if nicho_name and os.path.exists("temp_config.json"):
        os.remove("temp_config.json")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_processes = {
        pid: proc
        for pid, proc in active_processes.items()
        if pid.startswith(f"{chat_id}_")
    }

    if not user_processes:
        await update.message.reply_text("No hay procesos activos.")
        return

    status_text = "Procesos activos:\n\n"
    for pid, proc_info in user_processes.items():
        elapsed_time = asyncio.get_event_loop().time() - proc_info["start_time"]
        status_text += f"ID: {pid}\n"
        status_text += f"Nicho: {proc_info['nicho']}\n"
        status_text += f"Tiempo transcurrido: {int(elapsed_time)}s\n\n"

    keyboard = []
    for pid in user_processes.keys():
        keyboard.append(
            [InlineKeyboardButton(f"Cancelar {pid}", callback_data=f"cancel_{pid}")]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(status_text, reply_markup=reply_markup)


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_processes = {
        pid: proc
        for pid, proc in active_processes.items()
        if pid.startswith(f"{chat_id}_")
    }

    if not user_processes:
        await update.message.reply_text("No hay procesos activos para cancelar.")
        return

    if context.args and context.args[0] in user_processes:
        process_id = context.args[0]
        await cancel_process(update, process_id)
    else:
        keyboard = []
        for pid in user_processes.keys():
            keyboard.append(
                [InlineKeyboardButton(f"Cancelar {pid}", callback_data=f"cancel_{pid}")]
            )

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Selecciona un proceso para cancelar:", reply_markup=reply_markup
        )


async def cancel_process(update, process_id):
    if process_id in active_processes:
        process = active_processes[process_id]["process"]
        process.terminate()
        await asyncio.sleep(2)
        if process.returncode is None:
            process.kill()

        del active_processes[process_id]

        if isinstance(update, Update):
            await update.message.reply_text(f"Proceso {process_id} cancelado.")
        else:
            await update.edit_message_text(f"Proceso {process_id} cancelado.")
    else:
        message = f"Proceso {process_id} no encontrado o ya finalizado."
        if isinstance(update, Update):
            await update.message.reply_text(message)
        else:
            await update.edit_message_text(message)


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("run_"):
        nicho_name = data[4:]
        chat_id = update.effective_chat.id
        await query.edit_message_text(
            f"Iniciando automatización para: {nicho_name if nicho_name != 'random' else 'Nicho aleatorio'}"
        )
        context.application.create_task(
            execute_automation(chat_id, nicho_name if nicho_name != "random" else None)
        )
    elif data.startswith("cancel_"):
        process_id = data[7:]
        await cancel_process(query, process_id)


def main() -> None:
    os.makedirs("log", exist_ok=True)
    load_dotenv()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        sys.exit(1)

    global application
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list_nichos", list_nichos))
    application.add_handler(CommandHandler("run", run_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CallbackQueryHandler(handle_button))

    application.run_polling()


if __name__ == "__main__":
    main()
