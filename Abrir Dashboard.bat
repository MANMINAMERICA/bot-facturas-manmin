@echo off
title Dashboard Facturas MANMIN
echo Conectando al servidor...
set API_URL=https://bot-facturas-manmin-production.up.railway.app
start http://localhost:8501
set API_URL=%API_URL%
python -m streamlit run app.py --server.port 8501
