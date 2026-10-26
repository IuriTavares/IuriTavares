"""Servidor local e API Oracle. Execute python painel/app.py na raiz do projeto."""
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from backend.oracle import QueryError, configuration_status, query

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def respond(self, status, body, mime='application/json; charset=utf-8'):
        data = json.dumps(body, ensure_ascii=False).encode() if isinstance(body, dict) else body
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(data)

    def local_request(self):
        host = self.headers.get('Host', '')
        origin = self.headers.get('Origin')
        return host in ('127.0.0.1:8001', 'localhost:8001') and (origin is None or origin == 'http://' + host)

    def do_GET(self):
        if not self.local_request():
            return self.respond(403, {'error': 'Origem não permitida.'})
        if self.path == '/api/oracle/status':
            return self.respond(200, configuration_status())
        if self.path in ('/', '/index.html'):
            return self.respond(200, (ROOT/'index.html').read_bytes(), 'text/html; charset=utf-8')
        self.respond(404, {'error': 'Rota não encontrada.'})

    def do_POST(self):
        if not self.local_request():
            return self.respond(403, {'error': 'Origem não permitida.'})
        if self.path != '/api/oracle/consultar':
            return self.respond(404, {'error': 'Rota não encontrada.'})
        if self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json':
            return self.respond(415, {'error': 'Envie application/json.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 2048:
                return self.respond(413, {'error': 'Tamanho da requisição inválido.'})
            payload = json.loads(self.rfile.read(length))
            self.respond(200, query(payload))
        except (ValueError, UnicodeError):
            self.respond(400, {'error': 'JSON inválido.'})
        except QueryError as exc:
            self.respond(exc.status, {'error': str(exc)})
        except Exception:
            self.respond(500, {'error': 'Falha interna ao processar a consulta.'})

if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', 8001), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
