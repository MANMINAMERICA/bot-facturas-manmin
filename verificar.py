"""Script de verificacion del sistema"""
import os
import sys

print("=" * 60)
print("VERIFICACION DEL SISTEMA DE FACTURAS HELISA")
print("=" * 60)

errors = []

print("\n1. Verificando estructura de archivos...")
required_files = [
    "bot/main.py",
    "bot/handlers/start.py",
    "bot/handlers/factura.py",
    "bot/handlers/admin.py",
    "bot/ocr/google_vision.py",
    "bot/database/db.py",
    "bot/helisa/generador.py",
    "dashboard/app.py",
    "config/cuentas.json",
    "requirements.txt",
    ".env",
    "README.md",
]

base_path = os.path.dirname(os.path.abspath(__file__))
for f in required_files:
    full_path = os.path.join(base_path, f)
    if os.path.exists(full_path):
        print(f"  OK: {f}")
    else:
        print(f"  FALTA: {f}")
        errors.append(f"Falta archivo: {f}")

print("\n2. Verificando base de datos...")
db_path = os.path.join(base_path, "data", "facturas.db")
if os.path.exists(db_path):
    print("  OK: Base de datos existe")
else:
    print("  INFO: Base de datos se creara al iniciar el bot")

print("\n3. Verificando configuracion...")
env_path = os.path.join(base_path, ".env")
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        content = f.read()
        if "PEGA_TU_TOKEN_AQUI" in content:
            print("  PENDIENTE: Configura tu TELEGRAM_BOT_TOKEN en .env")
        else:
            print("  OK: TELEGRAM_BOT_TOKEN configurado")

        if "PEGA_TU_API_KEY_AQUI" in content:
            print("  PENDIENTE: Configura tu GOOGLE_VISION_API_KEY en .env")
        else:
            print("  OK: GOOGLE_VISION_API_KEY configurada")

        if "PEGA_TU_ID_AQUI" in content:
            print("  PENDIENTE: Configura tu ADMIN_IDS en .env")
        else:
            print("  OK: ADMIN_IDS configurado")
else:
    print("  ERROR: Archivo .env no encontrado")

print("\n4. Verificando cuentas contables...")
cuentas_path = os.path.join(base_path, "config", "cuentas.json")
if os.path.exists(cuentas_path):
    import json
    with open(cuentas_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        count = len(data.get('cuentas_comunes', []))
        print(f"  OK: {count} cuentas configuradas")
else:
    print("  ERROR: Archivo cuentas.json no encontrado")
    errors.append("Falta config/cuentas.json")

print("\n5. Verificando dependencias...")
try:
    import telegram
    print("  OK: python-telegram-bot instalado")
except ImportError:
    print("  PENDIENTE: Ejecuta 'pip install -r requirements.txt'")
    errors.append("Falta instalar dependencias")

print("\n" + "=" * 60)
if errors:
    print("ERRORES ENCONTRADOS:")
    for e in errors:
        print(f"  - {e}")
else:
    print("TODO LISTO! Sigue estos pasos:")
    print("1. Configura el token de Telegram en .env")
    print("2. Configura la API key de Google Vision en .env")
    print("3. Ejecuta: pip install -r requirements.txt")
    print("4. Ejecuta: cd bot && python main.py")
    print("5. En otra terminal: streamlit run dashboard/app.py")
print("=" * 60)
