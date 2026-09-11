"""Modulo de parsing de facturas con Google Gemini"""
import os
import json
import logging
import google.generativeai as genai

try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except ImportError:
    pass

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

def configure_gemini():
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)

def parse_invoice_with_ai(ocr_text):
    """Usa Google Gemini para extraer datos de la factura"""
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY no configurada, usando parseo basico")
        return None

    configure_gemini()

    model = genai.GenerativeModel('gemini-3.6-flash')

    prompt = f"""Eres un experto en facturas colombianas. Extrae los siguientes datos del texto OCR de una factura.

TEXTO OCR:
{ocr_text}

Responde SOLO con un JSON valido (sin markdown, sin ```), con esta estructura exacta:
{{
    "proveedor": "nombre del proveedor o empresa emisora",
    "nit_proveedor": "NIT del proveedor con guion y digito de verificacion",
    "numero": "numero de factura electronica (formato FEXXXXXXXX o numero de factura)",
    "fecha": "fecha de emision en formato YYYY-MM-DD",
    "subtotal": 0,
    "iva": 0,
    "retefuente": 0,
    "reteiva": 0,
    "reteica": 0,
    "total": 0,
    "total_pagado": 0,
    "concepto": "descripcion del servicio o producto"
}}

REGLAS:
- Si un campo no se encuentra, pon 0 para numeros o "" para texto
- El "total_pagado" es lo que realmente se paga (total menos retenciones)
- "retefuente" puede aparecer como "reterenta", "reterente", "ret fuente", "rt fte"
- La "fecha" debe ser la de EMISION, no la de autorizacion
- El "numero" debe ser el de la FACTURA, no el de autorizacion
- Si hay "RETE renta" o "rete renta", es retefuente
- Ignora codigos QR, CUFE, firmas digitales"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Limpiar respuesta
        if text.startswith('```'):
            text = text.split('\n', 1)[1]
        if text.endswith('```'):
            text = text.rsplit('```', 1)[0]
        text = text.strip()

        data = json.loads(text)

        # Validar que tenga los campos minimos
        required_fields = ['proveedor', 'numero', 'total']
        for field in required_fields:
            if field not in data:
                data[field] = '' if field != 'total' else 0

        return data

    except json.JSONDecodeError as e:
        logger.error(f"Error parseando JSON de Gemini: {e}")
        logger.error(f"Respuesta: {text}")
        return None
    except Exception as e:
        logger.error(f"Error llamando a Gemini: {e}")
        return None
