"""Modulo de OCR con Google Cloud Vision API + Gemini para parseo"""
import os
import re
import logging
import requests
import base64

try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except ImportError:
    pass

logger = logging.getLogger(__name__)

GOOGLE_VISION_API_KEY = os.getenv('GOOGLE_VISION_API_KEY')

def extract_text_from_image(image_path):
    if not GOOGLE_VISION_API_KEY:
        logger.error("GOOGLE_VISION_API_KEY no configurada")
        return ""

    with open(image_path, 'rb') as f:
        image_content = base64.b64encode(f.read()).decode('utf-8')

    url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_VISION_API_KEY}"

    payload = {
        "requests": [
            {
                "image": {"content": image_content},
                "features": [{"type": "TEXT_DETECTION", "maxResults": 1}]
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()

        if 'responses' in result and result['responses']:
            annotations = result['responses'][0].get('textAnnotations', [])
            if annotations:
                desc = annotations[0].get('description', '')
                return desc

        return ""
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en Google Vision API: {e}")
        return ""

def parse_invoice_data(text):
    """Intenta parsear con Gemini primero, si falla usa regex"""
    # Intentar con Gemini
    try:
        from ocr.gemini_parser import parse_invoice_with_ai
        gemini_result = parse_invoice_with_ai(text)
        if gemini_result and gemini_result.get('total', 0) > 0:
            # Asegurar que tenga todos los campos
            default_data = {
                'proveedor': '',
                'nit_proveedor': '',
                'numero': '',
                'fecha': '',
                'total': 0.0,
                'subtotal': 0.0,
                'iva': 0.0,
                'retefuente': 0.0,
                'reteiva': 0.0,
                'reteica': 0.0,
                'total_pagado': 0.0,
                'concepto': '',
            }
            for key in default_data:
                if key not in gemini_result:
                    gemini_result[key] = default_data[key]

            # Calcular total_pagado si no viene
            if gemini_result.get('total_pagado', 0) == 0 and gemini_result.get('total', 0) > 0:
                retenciones = (gemini_result.get('retefuente', 0) +
                              gemini_result.get('reteiva', 0) +
                              gemini_result.get('reteica', 0))
                gemini_result['total_pagado'] = gemini_result['total'] - retenciones

            logger.info("Parseo exitoso con Gemini")
            return gemini_result
    except Exception as e:
        logger.warning(f"Gemini fallo, usando regex: {e}")

    # Fallback a regex
    return _parse_with_regex(text)

def _parse_monto_colombiano(text):
    """Parsea un monto en formato colombiano"""
    text = text.replace('$', '').strip()
    if not text:
        return 0.0

    text = text.replace(' ', '')

    if ',' in text and '.' in text:
        dot_pos = text.rfind('.')
        comma_pos = text.rfind(',')
        if comma_pos > dot_pos:
            text = text.replace('.', '').replace(',', '.')
        else:
            text = text.replace(',', '')
    elif ',' in text:
        parts = text.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            text = text.replace(',', '.')
        else:
            text = text.replace(',', '')
    elif '.' in text:
        parts = text.split('.')
        if len(parts) == 2 and len(parts[1]) <= 2:
            pass
        else:
            text = text.replace('.', '')

    try:
        return float(text)
    except ValueError:
        return 0.0

def _find_amount_after_keyword(line, keywords):
    line_lower = line.lower()
    for kw in keywords:
        pattern = r'\b' + re.escape(kw) + r'\b'
        m = re.search(pattern, line_lower)
        if m:
            after = line[m.end():]
            m2 = re.search(r'[:\s$]*([\d][\d\.\,\s]*\d)', after)
            if m2:
                raw = m2.group(1).strip()
                val = _parse_monto_colombiano(raw)
                if val > 0:
                    return val
    return 0.0

def _parse_with_regex(text):
    """Parseo con regex como fallback"""
    lines = text.split('\n')

    data = {
        'proveedor': '',
        'nit_proveedor': '',
        'numero': '',
        'fecha': '',
        'total': 0.0,
        'subtotal': 0.0,
        'iva': 0.0,
        'retefuente': 0.0,
        'reteiva': 0.0,
        'reteica': 0.0,
        'total_pagado': 0.0,
        'concepto': '',
    }

    for i, line in enumerate(lines):
        line_s = line.strip()
        line_lower = line_s.lower()

        if not line_s:
            continue

        # PROVEEDOR
        if not data['proveedor']:
            m = re.search(r'(?:RAZON\s*SOCIAL|PROVEEDOR|NOMBRE\s*COMERCIAL|EMPRESA)\s*[:;]?\s*(.+)', line_s, re.IGNORECASE)
            if m:
                data['proveedor'] = m.group(1).strip()[:60]
            elif 'nit' in line_lower and i > 0:
                prev = lines[i-1].strip()
                if len(prev) > 5 and 'nit' not in prev.lower():
                    data['proveedor'] = prev[:60]

        # NIT DEL PROVEEDOR
        if not data['nit_proveedor']:
            m = re.search(r'NIT\s*[:;]?\s*(\d[\d\-\.]{6,20})', line_s, re.IGNORECASE)
            if m:
                data['nit_proveedor'] = m.group(1).strip()

        # NUMERO DE FACTURA
        if not data['numero']:
            m = re.search(r'\b(FE\d{6,15})\b', line_s)
            if m:
                data['numero'] = m.group(1)[:25]
            else:
                m = re.search(r'(?:No|No\.)\s*([A-Z0-9][\w\-]{4,20})', line_s, re.IGNORECASE)
                if m:
                    val = m.group(1).strip()
                    if not re.match(r'^\d{4}', val) and '-' not in val[:3]:
                        data['numero'] = val[:25]

        # FECHA - buscar "fecha de emision"
        if not data['fecha']:
            m = re.search(r'(?:fecha\s*(?:de\s*)?(?:emisi[oó]n|venta|expedici[oó]n|factura))\s*[:;]?\s*(\d{4}[\-\/]\d{2}[\-\/]\d{2})', line_lower)
            if m:
                data['fecha'] = m.group(1)
            else:
                m = re.search(r'(?:fecha\s*(?:de\s*)?(?:emisi[oó]n|venta|expedici[oó]n|factura))\s*[:;]?\s*(\d{1,2}[\s/\-\.]\d{1,2}[\s/\-\.]\d{2,4})', line_lower)
                if m:
                    data['fecha'] = m.group(1)
                else:
                    if not data['fecha']:
                        m = re.search(r'(\d{4}[\-\/]\d{2}[\-\/]\d{2})', line_s)
                        if m:
                            if i > 0 and 'autorizacion' not in lines[i-1].lower():
                                data['fecha'] = m.group(1)

        # TOTAL
        if data['total'] == 0:
            m = re.search(r'TOTAL\s*[:\$=]*\s*\$?\s*([\d\.\,\s]+)', line_s, re.IGNORECASE)
            if m:
                raw = m.group(1).strip()
                val = _parse_monto_colombiano(raw)
                if 100 < val < 10000000000:
                    data['total'] = val

        # SUBTOTAL
        if data['subtotal'] == 0:
            m = re.search(r'SUBTOTAL\s*[:\$=]*\s*\$?\s*([\d\.\,\s]+)', line_s, re.IGNORECASE)
            if m:
                raw = m.group(1).strip()
                val = _parse_monto_colombiano(raw)
                if 100 < val < 10000000000:
                    data['subtotal'] = val

        # IVA
        if data['iva'] == 0:
            m = re.search(r'IVA\s*(?:19\s*%?)?\s*[:\$=]*\s*\$?\s*([\d\.\,\s]+)', line_s, re.IGNORECASE)
            if m:
                raw = m.group(1).strip()
                val = _parse_monto_colombiano(raw)
                if 0 <= val < 1000000000:
                    data['iva'] = val

        # RETEFUENTE
        if data['retefuente'] == 0:
            retefuente_patterns = [
                r'(?:retefuente|ret\.?\s*fuente|reterenta|reterente|ret\.?\s*renta|rt\.?\s*fuente)',
            ]
            for pattern in retefuente_patterns:
                m = re.search(pattern, line_lower)
                if m:
                    after = line[m.end():]
                    m2 = re.search(r'[:\s$]*([\d][\d\.\,\s]*\d)', after)
                    if m2:
                        raw = m2.group(1).strip()
                        val = _parse_monto_colombiano(raw)
                        if 0 <= val < 1000000000:
                            data['retefuente'] = val
                            break

        # RETEIVA
        if data['reteiva'] == 0:
            m = re.search(r'(?:reteiva|ret\.?\s*iva)\s*[:\$=]*\s*\$?\s*([\d\.\,\s]+)', line_s, re.IGNORECASE)
            if m:
                raw = m.group(1).strip()
                val = _parse_monto_colombiano(raw)
                if 0 <= val < 1000000000:
                    data['reteiva'] = val

        # RETEICA
        if data['reteica'] == 0:
            m = re.search(r'(?:reteica|ret\.?\s*ica)\s*[:\$=]*\s*\$?\s*([\d\.\,\s]+)', line_s, re.IGNORECASE)
            if m:
                raw = m.group(1).strip()
                val = _parse_monto_colombiano(raw)
                if 0 <= val < 1000000000:
                    data['reteica'] = val

        # CONCEPTO
        if not data['concepto']:
            m = re.search(r'(?:DESCRIPCION|DETALLE|CONCEPTO|OBJETO|BIEN|SERVICIO|PRODUCTO)\s*(?:DEL\s*(?:PRODUCTO|SERVICIO|BIEN))?\s*[:;]\s*(.+)', line_s, re.IGNORECASE)
            if m:
                concep = m.group(1).strip()
                if len(concep) > 3 and not re.match(r'^[\d\.\,\$\s]+$', concep):
                    data['concepto'] = concep[:60]

    # Fallback: buscar $ mas grande para total
    if data['total'] == 0:
        for match in re.finditer(r'\$\s*([\d\.\,\s]+)', text):
            val = _parse_monto_colombiano(match.group(1))
            if 1000 < val < 10000000000:
                if val > data['total']:
                    data['total'] = val

    # Calcular total pagado
    total_retenciones = data['retefuente'] + data['reteiva'] + data['reteica']
    if data['total'] > 0:
        data['total_pagado'] = data['total'] - total_retenciones
    else:
        data['total_pagado'] = data['total']

    if data['subtotal'] == 0 and data['total'] > 0:
        data['subtotal'] = data['total']

    return data
