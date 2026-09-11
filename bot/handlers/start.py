"""Handler para comandos de inicio"""
import os
from telegram import Update
from telegram.ext import ContextTypes
from database.db import is_user_registered, add_user

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name

    admin_ids = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()]
    if user_id in admin_ids and not is_user_registered(user_id):
        add_user(user_id, username)

    if is_user_registered(user_id):
        await update.message.reply_text(
            f"¡Bienvenido {username}!\n\n"
            "Puedes enviarme facturas (foto o PDF) para procesarlas.\n\n"
            "Comandos disponibles:\n"
            "/start - Ver este mensaje\n"
            "/admin - Panel de administración (solo admins)"
        )
    else:
        await update.message.reply_text(
            f"Hola {username}, no tienes acceso al bot.\n\n"
            "Tu ID de Telegram es: " + str(user_id) + "\n\n"
            "Envía este ID al administrador para que te agregue."
        )
