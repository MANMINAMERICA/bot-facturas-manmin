"""Dashboard web con Streamlit - conecta a API de Railway"""
import os
import sys
import json
import requests
import pandas as pd
import streamlit as st
from datetime import datetime

API_URL = os.getenv('API_URL', 'https://bot-facturas-manmin-production.up.railway.app')

st.set_page_config(page_title="Facturas HELISA - Iglesia MANMIN", page_icon="📊", layout="wide")

st.title("Dashboard de Facturas HELISA")
st.caption("Iglesia MANMIN Colombia - Sistema de gestion de facturas")

@st.cache_data(ttl=30)
def load_cuentas():
    import json
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'cuentas.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)['cuentas_comunes']

@st.cache_data(ttl=30)
def load_facturas():
    try:
        resp = requests.get(f"{API_URL}/api/facturas", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return []

cuentas = load_cuentas()
cuentas_dict = {c['codigo']: c['nombre'] for c in cuentas}

tab_pendientes, tab_historial = st.tabs(["Cola de Facturas", "Historial"])

with tab_pendientes:
    st.header("Cola de Facturas Pendientes")

    facturas = load_facturas()
    pendientes = [f for f in facturas if f.get('estado') == 'pendiente']

    if not pendientes:
        st.info("No hay facturas pendientes. Envia facturas por Telegram para que aparezcan aqui.")
    else:
        st.metric("Facturas pendientes", len(pendientes))

        for f in pendientes:
            account_name = cuentas_dict.get(f.get('cuenta', ''), f.get('cuenta', ''))
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
                with col1:
                    st.write(f"**{f.get('proveedor', 'N/A')}**")
                    st.caption(f"NIT: {f.get('nit_proveedor', 'N/A')} | Factura: {f.get('numero', 'N/A')}")
                with col2:
                    st.write(f"Fecha: {f.get('fecha', 'N/A')}")
                    st.write(f"Subtotal: ${f.get('subtotal', 0):,.0f}")
                with col3:
                    st.write(f"IVA: ${f.get('iva', 0):,.0f}")
                    st.write(f"Total: ${f.get('total', 0):,.0f}")
                with col4:
                    st.write(f"Retefuente: ${f.get('retefuente', 0):,.0f}")
                    st.write(f"**Total Pagado: ${f.get('total_pagado', 0):,.0f}**")
                with col5:
                    st.write(f"Cuenta: {f.get('cuenta', 'N/A')}")
                    st.caption(account_name[:30] if account_name else "")

with tab_historial:
    st.header("Historial de Facturas")

    facturas = load_facturas()

    if not facturas:
        st.info("No hay facturas registradas aun.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            filtro_estado = st.selectbox("Filtrar por estado", ["Todos", "pendiente", "procesada", "importada"])
        with col2:
            filtro_proveedor = st.text_input("Buscar proveedor")
        with col3:
            filtro_cuenta = st.selectbox("Filtrar por cuenta", ["Todas"] + [f"{c['codigo']} - {c['nombre']}" for c in cuentas])

        df_filtrado = facturas.copy()
        if filtro_estado != "Todos":
            df_filtrado = [f for f in df_filtrado if f.get('estado') == filtro_estado]
        if filtro_proveedor:
            df_filtrado = [f for f in df_filtrado if filtro_proveedor.lower() in f.get('proveedor', '').lower()]
        if filtro_cuenta != "Todas":
            codigo = filtro_cuenta.split(" - ")[0]
            df_filtrado = [f for f in df_filtrado if f.get('cuenta') == codigo]

        st.write(f"Mostrando {len(df_filtrado)} de {len(facturas)} facturas")

        if df_filtrado:
            df = pd.DataFrame(df_filtrado)
            cols_show = ['proveedor', 'nit_proveedor', 'numero', 'fecha', 'subtotal', 'iva', 'retefuente', 'total', 'total_pagado', 'cuenta', 'estado']
            cols_available = [c for c in cols_show if c in df.columns]
            st.dataframe(df[cols_available], use_container_width=True)

st.divider()
st.caption("Sistema de gestion de facturas HELISA - Iglesia MANMIN Colombia")
