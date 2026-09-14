"""API simple para servir datos de facturas"""
import os
import json
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler

DB_PATH = os.getenv('DATABASE_PATH', os.path.join(os.path.dirname(__file__), 'data', 'facturas.db'))

class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/facturas':
            try:
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM facturas ORDER BY fecha_registro DESC")
                facturas = [dict(row) for row in cursor.fetchall()]
                conn.close()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(facturas, default=str).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        elif self.path == '/api/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, format, *args):
        pass

def main():
    port = int(os.getenv('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), APIHandler)
    print(f"API corriendo en puerto {port}")
    server.serve_forever()

if __name__ == '__main__':
    main()
