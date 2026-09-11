"""Modulo para generar archivos de importacion para HELISA"""
import os
import pandas as pd
import sqlite3
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
DB_PATH = os.path.join(DB_DIR, 'facturas.db')
EXPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'exports')

def generate_helisa_import():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM facturas WHERE estado = 'pendiente'", conn)
    conn.close()

    if df.empty:
        return None

    export_df = pd.DataFrame({
        'Tipo Documento': ['Factura'] * len(df),
        'Numero': df['numero'],
        'Fecha': df['fecha'],
        'Proveedor': df['proveedor'],
        'Concepto': df['concepto'],
        'Total': df['total'],
        'Cuenta Contable': df['cuenta'],
    })

    os.makedirs(EXPORTS_DIR, exist_ok=True)
    filename = f"helisa_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(EXPORTS_DIR, filename)
    export_df.to_excel(filepath, index=False, engine='openpyxl')

    return filepath
