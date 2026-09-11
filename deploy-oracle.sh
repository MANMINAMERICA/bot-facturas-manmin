#!/bin/bash
# Script de despliegue para Oracle Cloud
# Ejecutar en la VM despues de crearla

echo "=== Instalando dependencias ==="
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv

echo "=== Creando entorno virtual ==="
python3 -m venv venv
source venv/bin/activate

echo "=== Instalando paquetes ==="
pip install -r requirements-cloud.txt

echo "=== Configurando variables de entorno ==="
cat > .env << EOF
TELEGRAM_BOT_TOKEN=8894684119:AAEgUWXWPrDjmrkxFFqnJVC1Y4Z95t-AIYE
GOOGLE_VISION_API_KEY=AIzaSyDlTp0srAhpr2yNLL4yFunZQdIXipPrm1A
GEMINI_API_KEY=AQ.Ab8RN6IFVHetEBA9mzMFs2maEtK8uyauL5qaoLXeIAfiit-Erg
EOF

echo "=== Iniciando bot ==="
python bot/main.py
