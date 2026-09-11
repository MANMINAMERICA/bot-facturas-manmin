"""Dashboard web con Streamlit para gestion de facturas HELISA"""
import os
import sys
import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bot'))

DB_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
DB_PATH = os.path.join(DB_DIR, 'facturas.db')
EXPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'exports')

st.set_page_config(page_title="Facturas HELISA - Iglesia MANMIN", page_icon="📊", layout="wide")

st.title("Dashboard de Facturas HELISA")
st.caption("Iglesia MANMIN Colombia - Sistema de gestion de facturas")

def get_conn():
    os.makedirs(DB_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def load_cuentas():
    import json
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'cuentas.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)['cuentas_comunes']

cuentas = load_cuentas()
cuentas_dict = {c['codigo']: c['nombre'] for c in cuentas}

tab_pendientes, tab_historial, tab_generar = st.tabs([
    "Cola de Facturas", "Historial", "Generar Archivo HELISA"
])

with tab_pendientes:
    st.header("Cola de Facturas Pendientes")

    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT id, proveedor, nit_proveedor, numero, fecha, subtotal, iva, retefuente, reteiva, reteica, total, total_pagado, cuenta, concepto, estado, fecha_registro "
        "FROM facturas WHERE estado = 'pendiente' ORDER BY fecha_registro DESC",
        conn,
    )
    conn.close()

    if df.empty:
        st.info("No hay facturas pendientes. Envia facturas por Telegram para que aparezcan aqui.")
    else:
        st.metric("Facturas pendientes", len(df))

        for _, row in df.iterrows():
            account_name = cuentas_dict.get(row['cuenta'], row['cuenta'])
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
                with col1:
                    st.write(f"**{row['proveedor']}**")
                    st.caption(f"NIT: {row['nit_proveedor'] or 'N/A'} | Factura: {row['numero']}")
                with col2:
                    st.write(f"Fecha: {row['fecha']}")
                    st.write(f"Subtotal: ${row['subtotal']:,.0f}")
                with col3:
                    st.write(f"IVA: ${row['iva']:,.0f}")
                    st.write(f"Total: ${row['total']:,.0f}")
                with col4:
                    st.write(f"Retefuente: ${row['retefuente']:,.0f}")
                    st.write(f"**Total Pagado: ${row['total_pagado']:,.0f}**")
                with col5:
                    st.write(f"Cuenta: {row['cuenta']}")
                    st.caption(account_name[:30])
                    if st.button("Marcar procesada", key=f"proc_{row['id']}"):
                        conn = get_conn()
                        conn.execute("UPDATE facturas SET estado = 'procesada' WHERE id = ?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()

        st.divider()
        if st.button("Marcar TODAS como procesadas", type="secondary"):
            conn = get_conn()
            conn.execute("UPDATE facturas SET estado = 'procesada' WHERE estado = 'pendiente'")
            conn.commit()
            conn.close()
            st.success("Todas las facturas marcadas como procesadas")
            st.rerun()

with tab_historial:
    st.header("Historial de Facturas")

    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT id, proveedor, nit_proveedor, numero, fecha, subtotal, iva, retefuente, total, total_pagado, cuenta, estado, fecha_registro "
        "FROM facturas ORDER BY fecha_registro DESC",
        conn,
    )
    conn.close()

    if df.empty:
        st.info("No hay facturas registradas aun.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            filtro_estado = st.selectbox("Filtrar por estado", ["Todos", "pendiente", "procesada", "importada"])
        with col2:
            filtro_proveedor = st.text_input("Buscar proveedor")
        with col3:
            filtro_cuenta = st.selectbox("Filtrar por cuenta", ["Todas"] + [f"{c['codigo']} - {c['nombre']}" for c in cuentas])

        df_filtrado = df.copy()
        if filtro_estado != "Todos":
            df_filtrado = df_filtrado[df_filtrado['estado'] == filtro_estado]
        if filtro_proveedor:
            df_filtrado = df_filtrado[df_filtrado['proveedor'].str.contains(filtro_proveedor, case=False, na=False)]
        if filtro_cuenta != "Todas":
            codigo = filtro_cuenta.split(" - ")[0]
            df_filtrado = df_filtrado[df_filtrado['cuenta'] == codigo]

        st.write(f"Mostrando {len(df_filtrado)} de {len(df)} facturas")

        if not df_filtrado.empty:
            df_display = df_filtrado[['proveedor', 'nit_proveedor', 'numero', 'fecha', 'subtotal', 'iva', 'retefuente', 'total', 'total_pagado', 'cuenta', 'estado']].copy()
            df_display.columns = ['Proveedor', 'NIT', 'Factura', 'Fecha', 'Subtotal', 'IVA', 'Retefuente', 'Total', 'Total Pagado', 'Cuenta', 'Estado']
            st.dataframe(df_display, use_container_width=True)
        else:
            st.dataframe(df_filtrado, use_container_width=True)

with tab_generar:
    st.header("Generar Archivo para HELISA")

    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT * FROM facturas WHERE estado = 'pendiente' ORDER BY fecha_registro",
        conn,
    )
    conn.close()

    if df.empty:
        st.info("No hay facturas pendientes para generar el archivo de importacion.")
    else:
        st.write(f"Facturas pendientes: **{len(df)}**")
        st.write(f"Total a pagar: **${df['total_pagado'].sum():,.0f}**")

        st.divider()

        df_export = df[['numero', 'fecha', 'proveedor', 'nit_proveedor', 'concepto', 'subtotal', 'iva', 'retefuente', 'reteiva', 'reteica', 'total', 'total_pagado', 'cuenta']].copy()
        df_export.columns = ['Factura N', 'Fecha', 'Proveedor', 'NIT', 'Concepto', 'Subtotal', 'IVA', 'Retefuente', 'ReteIVA', 'ReteICA', 'Total', 'Total Pagado', 'Cuenta Contable']
        df_export['Cuenta Contable'] = df_export['Cuenta Contable'].apply(
            lambda x: f"{x} - {cuentas_dict.get(x, '')}"
        )

        st.dataframe(df_export, use_container_width=True)

        os.makedirs(EXPORTS_DIR, exist_ok=True)
        filename = f"helisa_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(EXPORTS_DIR, filename)

        if st.button("Generar archivo Excel para HELISA", type="primary"):
            df_export.to_excel(filepath, index=False, engine='openpyxl')
            st.success(f"Archivo generado: {filename}")

            with open(filepath, 'rb') as f:
                st.download_button(
                    label="Descargar archivo",
                    data=f.read(),
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            st.info("Para importar en HELISA: Herramientas > Importar datos > Seleccionar este archivo")

st.divider()
st.caption("Sistema de gestion de facturas HELISA - Iglesia MANMIN Colombia")
