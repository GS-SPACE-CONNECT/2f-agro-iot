#!/usr/bin/env python3
"""
Mock local da API `/api/diagnostico` — pra testar o cliente sem subir o backend C#.

Uso:
    python tools/mock_api.py 5000
Depois, noutro terminal:
    python olho_na_folha.py --source amostras/ --api-url http://localhost:5000/api/diagnostico
"""
from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        tamanho = int(self.headers.get("Content-Length", 0))
        corpo = self.rfile.read(tamanho)
        try:
            dado = json.loads(corpo)
        except Exception:
            dado = corpo.decode("utf-8", "replace")
        print(f"[MOCK] POST {self.path} <- {dado}", flush=True)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def log_message(self, *args):  # silencia o log HTTP padrão
        return


if __name__ == "__main__":
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    print(f"[MOCK] ouvindo em http://localhost:{porta}/api/diagnostico  (Ctrl+C sai)")
    HTTPServer(("0.0.0.0", porta), Handler).serve_forever()
