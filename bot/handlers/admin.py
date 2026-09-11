"""Handler para comandos de administracion"""
import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.db import is_user_registered, add_user, list_users, delete_user

logger = logging.getLogger(__name__)

ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()]

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("No tienes permisos de administrador.")
        return

    await update.message.reply_text(
        "Panel de Administracion\n\n"
        "Comandos disponibles:\n\n"
        "/agregar_usuario <id_telegram> <nombre>\n"
        "  Ejemplo: /agregar_usuario 123456789 Juan Perez\n\n"
        "/listar_usuarios\n"
        "  Muestra todos los usuarios registrados\n\n"
        "/eliminar_usuario <id_telegram>\n"
        "  Elimina un usuario del sistema"
    )

async def add_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("No tienes permisos de administrador.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Uso: /agregar_usuario <id_telegram> <nombre>\n\n"
            "Ejemplo: /agregar_usuario 123456789 Juan Perez"
        )
        return

    try:
        telegram_id = int(args[0])
    except ValueError:
        await update.message.reply_text("El ID de Telegram debe ser un numero.")
        return

    name = ' '.join(args[1:])

    add_user(telegram_id, name)
    await update.message.reply_text(
        f"Usuario agregado!\n\n"
        f"Nombre: {name}\n"
        f"ID Telegram: {telegram_id}"
    )
    logger.info(f"Usuario agregado: {name} (ID: {telegram_id}) por admin {user_id}")

async def list_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("No tienes permisos de administrador.")
        return

    users = list_users()

    if not users:
        await update.message.reply_text("No hay usuarios registrados.")
        return

    text = "Usuarios registrados:\n\n"
    for u in users:
        text += f"  {u['nombre']} - ID: {u['telegram_id']}\n"

    text += f"\nTotal: {len(users)} usuarios"
    await update.message.reply_text(text)

async def delete_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("No tienes permisos de administrador.")
        return

    args = context.args
    if len(args) < 1:
        await update.message.reply_text(
            "Uso: /eliminar_usuario <id_telegram>"
        )
        return

    try:
        telegram_id = int(args[0])
    except ValueError:
        await update.message.reply_text("El ID de Telegram debe ser un numero.")
        return

    if not is_user_registered(telegram_id):
        await update.message.reply_text(f"No se encontro usuario con ID {telegram_id}")
        return

    delete_user(telegram_id)
    await update.message.reply_text(f"Usuario con ID {telegram_id} eliminado.")
    logger.info(f"Usuario eliminado: ID {telegram_id} por admin {user_id}")
