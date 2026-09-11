"""Modulo de base de datos SQLite"""
import os
import sqlite3
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
DB_PATH = os.path.join(DB_DIR, 'facturas.db')

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor TEXT NOT NULL,
            nit_proveedor TEXT,
            numero TEXT NOT NULL,
            fecha TEXT,
            total REAL,
            subtotal REAL DEFAULT 0,
            iva REAL DEFAULT 0,
            retefuente REAL DEFAULT 0,
            reteiva REAL DEFAULT 0,
            reteica REAL DEFAULT 0,
            total_pagado REAL DEFAULT 0,
            concepto TEXT,
            cuenta TEXT,
            estado TEXT DEFAULT 'pendiente',
            user_id INTEGER,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES usuarios(telegram_id)
        )
    ''')

    conn.commit()
    conn.close()

def _get_conn():
    os.makedirs(DB_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def is_user_registered(telegram_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM usuarios WHERE telegram_id = ?", (telegram_id,))
    result = cursor.fetchone() is not None
    conn.close()
    return result

def add_user(telegram_id, nombre):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO usuarios (telegram_id, nombre) VALUES (?, ?)",
        (telegram_id, nombre),
    )
    conn.commit()
    conn.close()

def list_users():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id, nombre FROM usuarios ORDER BY nombre")
    users = [{'telegram_id': row[0], 'nombre': row[1]} for row in cursor.fetchall()]
    conn.close()
    return users

def delete_user(telegram_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE telegram_id = ?", (telegram_id,))
    conn.commit()
    conn.close()

def save_invoice(proveedor, numero, fecha, total, concepto, cuenta, user_id,
                 subtotal=0, iva=0, nit_proveedor='', retefuente=0, reteiva=0, reteica=0, total_pagado=0):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO facturas
            (proveedor, nit_proveedor, numero, fecha, total, subtotal, iva, retefuente, reteiva, reteica, total_pagado, concepto, cuenta, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (proveedor, nit_proveedor, numero, fecha, total, subtotal, iva, retefuente, reteiva, reteica, total_pagado, concepto, cuenta, user_id))
    conn.commit()
    invoice_id = cursor.lastrowid
    conn.close()
    return invoice_id

def get_pending_invoices():
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM facturas WHERE estado = 'pendiente' ORDER BY fecha_registro DESC")
    invoices = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return invoices

def get_all_invoices():
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM facturas ORDER BY fecha_registro DESC")
    invoices = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return invoices

def update_invoice_status(invoice_id, status):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE facturas SET estado = ? WHERE id = ?", (status, invoice_id))
    conn.commit()
    conn.close()

def delete_invoice(invoice_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM facturas WHERE id = ?", (invoice_id,))
    conn.commit()
    conn.close()
