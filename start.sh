#!/bin/bash
# Script de inicio para Railway - Bot + Dashboard

echo "Iniciando Bot de Facturas MANMIN..."

# Iniciar bot en background
python bot/main.py &

echo "Iniciando Dashboard en puerto 8501..."

# Iniciar dashboard
python -m streamlit run dashboard/app.py \
    --server.port $PORT \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false

