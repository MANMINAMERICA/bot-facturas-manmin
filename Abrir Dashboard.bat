@echo off
title Dashboard Facturas MANMIN
echo Abriendo Dashboard de Facturas...
start http://localhost:8501
python -m streamlit run app.py --server.port 8501
