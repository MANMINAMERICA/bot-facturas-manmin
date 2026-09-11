"""Handler para recibir y procesar facturas"""
import os
import json
import logging
import fitz
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db import save_invoice, is_user_registered
from ocr.google_vision import extract_text_from_image, parse_invoice_data

logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'cuentas.json')

def load_cuentas():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)['cuentas_comunes']

def pdf_to_image(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        page = doc[0]
        pix = page.get_pixmap(dpi=200)
        img_path = pdf_path.replace('.pdf', '.jpg')
        pix.save(img_path)
        doc.close()
        return img_path
    except Exception as e:
        logger.error(f"Error convirtiendo PDF a imagen: {e}")
        raise

async def receive_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_user_registered(user_id):
        await update.message.reply_text("No tienes acceso al bot.")
        return

    photo = update.message.photo[-1] if update.message.photo else None
    document = update.message.document

    if photo:
        file = await context.bot.get_file(photo.file_id)
        ext = "jpg"
    elif document and document.mime_type == 'application/pdf':
        file = await context.bot.get_file(document.file_id)
        ext = "pdf"
    else:
        await update.message.reply_text("Por favor envia una foto o PDF de la factura.")
        return

    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    temp_path = os.path.join(data_dir, f"temp_{user_id}.{ext}")

    try:
        await file.download_to_drive(temp_path)
    except Exception as e:
        logger.error(f"Error descargando archivo: {e}")
        await update.message.reply_text("Error al descargar el archivo. Intenta de nuevo.")
        return

    await update.message.reply_text("Procesando factura con OCR...")

    try:
        if ext == "pdf":
            img_path = pdf_to_image(temp_path)
            text = extract_text_from_image(img_path)
            try:
                os.remove(img_path)
            except OSError:
                pass
        else:
            text = extract_text_from_image(temp_path)
    except Exception as e:
        logger.error(f"Error en OCR: {e}")
        await update.message.reply_text(f"Error al procesar la imagen: {str(e)[:100]}")
        try:
            os.remove(temp_path)
        except OSError:
            pass
        return

    try:
        os.remove(temp_path)
    except OSError:
        pass

    if not text.strip():
        await update.message.reply_text(
            "No se pudo extraer texto de la imagen.\n"
            "Intenta con una foto mas clara o envia el PDF."
        )
        return

    invoice_data = parse_invoice_data(text)

    context.user_data['invoice_data'] = invoice_data
    context.user_data['raw_text'] = text

    keyboard = [
        [
            InlineKeyboardButton("Confirmar", callback_data="confirmar"),
            InlineKeyboardButton("Rechazar", callback_data="rechazar"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Datos extraidos:\n\n"
        f"Proveedor: {invoice_data['proveedor']}\n"
        f"NIT: {invoice_data['nit_proveedor']}\n"
        f"Factura N: {invoice_data['numero']}\n"
        f"Fecha: {invoice_data['fecha']}\n"
        f"Subtotal: ${invoice_data['subtotal']:,.0f}\n"
        f"IVA: ${invoice_data['iva']:,.0f}\n"
        f"Retefuente: ${invoice_data['retefuente']:,.0f}\n"
        f"Total: ${invoice_data['total']:,.0f}\n"
        f"Total Pagado: ${invoice_data['total_pagado']:,.0f}\n"
        f"Concepto: {invoice_data['concepto']}\n\n"
        f"Es correcto?",
        reply_markup=reply_markup,
    )

async def confirm_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cuentas = load_cuentas()

    buttons = []
    for i in range(0, len(cuentas), 2):
        row = []
        for j in range(2):
            if i + j < len(cuentas):
                c = cuentas[i + j]
                row.append(InlineKeyboardButton(
                    f"{c['codigo']} - {c['nombre'][:30]}",
                    callback_data=f"cuenta_{c['codigo']}"
                ))
        buttons.append(row)

    reply_markup = InlineKeyboardMarkup(buttons)

    await query.edit_message_text(
        "Selecciona la cuenta contable:",
        reply_markup=reply_markup,
    )

async def reject_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data.clear()

    await query.edit_message_text("Factura descartada. Puedes enviar otra cuando quieras.")

async def select_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    account_code = query.data.replace("cuenta_", "")
    invoice_data = context.user_data.get('invoice_data')

    if not invoice_data:
        await query.edit_message_text("Error: no se encontraron datos de la factura. Envia la factura de nuevo.")
        return

    cuentas = load_cuentas()
    account_name = ""
    for c in cuentas:
        if c['codigo'] == account_code:
            account_name = c['nombre']
            break

    invoice_id = save_invoice(
        proveedor=invoice_data['proveedor'],
        numero=invoice_data['numero'],
        fecha=invoice_data['fecha'],
        total=invoice_data['total'],
        concepto=invoice_data['concepto'],
        cuenta=account_code,
        user_id=query.from_user.id,
        subtotal=invoice_data['subtotal'],
        iva=invoice_data['iva'],
        nit_proveedor=invoice_data['nit_proveedor'],
        retefuente=invoice_data['retefuente'],
        reteiva=invoice_data['reteiva'],
        reteica=invoice_data['reteica'],
        total_pagado=invoice_data['total_pagado'],
    )

    context.user_data.clear()

    await query.edit_message_text(
        f"Factura #{invoice_id} guardada!\n\n"
        f"Cuenta: {account_code} - {account_name}\n"
        f"Estado: Pendiente de importar a HELISA\n\n"
        f"Ver en dashboard: http://localhost:8501"
    )
