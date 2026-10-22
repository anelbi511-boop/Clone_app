"""Minimal local development server. No proprietary HL Studio modules included."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import json
import os
import uuid

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / 'frontend'
DATA = Path(os.environ.get('CLONE_APP_DATA', str(ROOT / 'data')))
PROJECTS = DATA / 'projects'
PROJECTS.mkdir(parents=True, exist_ok=True)

class Handler(BaseHTTPRequestHandler):
    def _send(self, payload, code=200):
        raw = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/health':
            return self._send({'ok': True, 'app': 'Clone App MVP'})
        if path == '/api/projects':
            items = []
            for f in sorted(PROJECTS.glob('*.json')):
                try:
                    items.append(json.loads(f.read_text(encoding='utf-8')))
                except (OSError, ValueError):
                    continue
            return self._send({'ok': True, 'projects': items})
        filename = 'index.html' if path == '/' else path.lstrip('/')
        file = (WEB / filename).resolve()
        if not file.is_relative_to(WEB.resolve()) or not file.is_file():
            return self.send_error(404)
        typ = {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8'}.get(file.suffix,'application/octet-stream')
        raw = file.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', typ)
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        if urlparse(self.path).path != '/api/projects':
            return self._send({'ok':False,'error':'Not found'},404)
        try:
            size = int(self.headers.get('Content-Length','0'))
            if not 0 < size <= 1_000_000:
                return self._send({'ok':False,'error':'Invalid payload size'},413)
            obj = json.loads(self.rfile.read(size))
            name = str(obj.get('name','')).strip()[:100]
            if not name:
                return self._send({'ok':False,'error':'Project name required'},400)
            item = {'id':uuid.uuid4().hex,'name':name,'notes':str(obj.get('notes',''))[:5000]}
            (PROJECTS / (item['id']+'.json')).write_text(json.dumps(item,ensure_ascii=False), encoding='utf-8')
            return self._send({'ok':True,'project':item},201)
        except (ValueError, TypeError, OSError):
            return self._send({'ok':False,'error':'Invalid JSON or storage error'},400)

if __name__ == '__main__':
    host, port = '127.0.0.1', int(os.environ.get('PORT','8790'))
    print(f'Open http://{host}:{port}')
    ThreadingHTTPServer((host,port),Handler).serve_forever()
