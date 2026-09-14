"""Bot de Telegram para gestión de facturas HELISA"""
import os
import logging
import sys
import subprocess
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from handlers.start import start_command
from handlers.factura import receive_invoice, confirm_invoice, reject_invoice, select_account
from handlers.admin import admin_command, add_user_command, list_users_command, delete_user_command
from database.db import init_db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def start_api_server():
    try:
        subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), 'api_server.py')])
        print("API server iniciado")
    except Exception as e:
        print(f"API server error: {e}")

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: No se encontró TELEGRAM_BOT_TOKEN")
        return

    init_db()

    start_api_server()

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("agregar_usuario", add_user_command))
    app.add_handler(CommandHandler("listar_usuarios", list_users_command))
    app.add_handler(CommandHandler("eliminar_usuario", delete_user_command))

    app.add_handler(CallbackQueryHandler(confirm_invoice, pattern="^confirmar$"))
    app.add_handler(CallbackQueryHandler(reject_invoice, pattern="^rechazar$"))
    app.add_handler(CallbackQueryHandler(select_account, pattern="^cuenta_"))

    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.PDF, receive_invoice))

    logger.info("Bot de facturas HELISA iniciado")
    print("Bot iniciado. Presiona Ctrl+C para detener.")
    app.run_polling()

if __name__ == '__main__':
    main()
