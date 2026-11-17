"""Run a real-browser UI smoke check with synthetic stubbed authentication.

It does not test OIDC, trust a certificate, or connect to an existing server.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory, gettempdir
from threading import Thread
from urllib.parse import urlsplit
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def browser_path():
    candidates = [os.environ.get('NAWA_TEST_BROWSER'), shutil.which('msedge'),
                  shutil.which('google-chrome'), shutil.which('chromium')]
    if sys.platform == 'win32':
        for base in (os.environ.get('ProgramFiles(x86)'), os.environ.get('ProgramFiles')):
            if base:
                candidates.extend([str(Path(base) / 'Microsoft/Edge/Application/msedge.exe'),
                                   str(Path(base) / 'Google/Chrome/Application/chrome.exe')])
    return next((value for value in candidates if value and Path(value).is_file()), None)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, content, kind='application/json', cookie=None, status=200):
        raw = content if isinstance(content, bytes) else json.dumps(content).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'")
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/':
            html = (ROOT / 'web/index.html').read_text(encoding='utf-8')
            html = html.replace('</body>', '<script src="/browser_intake_mock.js" defer></script></body>')
            return self.send(html.encode(), 'text/html; charset=utf-8')
        if path in ('/app.js', '/style.css'):
            return self.send((ROOT / 'web' / path[1:]).read_bytes(),
                             'text/javascript' if path.endswith('.js') else 'text/css')
        if path == '/browser_intake_mock.js':
            return self.send((ROOT / 'tests/browser_intake_mock.js').read_bytes(), 'text/javascript')
        if path == '/auth/config': return self.send({'mode':'oidc','intake_enabled':True})
        if path == '/auth/me': return self.send({'role':'analyst'}, cookie='nawa_csrf=synthetic-csrf; Path=/; SameSite=Lax')
        if path == '/api/quotations': return self.send({'quotations':[], 'storage':'postgres'})
        if path == '/api/intake/documents': return self.send({'documents':[{'id':'demo-id','filename':'synthetic.txt','state':'completed','attempts':1}]})
        if path == '/api/intake/status': return self.send({'state':'completed','attempts':1})
        if path == '/api/intake/result': return self.send({'result':{'supplier':'Synthetic supplier','total':'1050.00'}})
        self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', '0'))
        if length < 1 or length > 1024 * 1024 or self.headers.get('X-NAWA-CSRF') != 'synthetic-csrf':
            return self.send_error(403)
        payload = json.loads(self.rfile.read(length))
        if self.path == '/api/intake/batch' and payload['files'][0]['filename'] == 'synthetic.txt':
            return self.send({'files':[{'id':'demo-id','created':True}]})
        if self.path == '/api/intake/promote' and payload['id'] == 'demo-id':
            return self.send({'id':'quote1','created':True,'quotation':{'document':'synthetic.txt',
                'supplier':'Synthetic supplier','currency':'AED','subtotal':'1000.00','vat_rate_percent':'5.00',
                'vat_amount':'50.00','total':'1050.00','checks':{'valid':True},'evidence':{}}})
        if self.path == '/api/review/show':
            if not getattr(self.server, 'synthetic_review_started', False):
                return self.send({'error':'Review is not initialized'}, status=404)
            return self.send({'status':'pending_review','revision':1,'history':[]})
        if self.path == '/api/review/start':
            self.server.synthetic_review_started = True
            return self.send({'status':'pending_review','revision':1,'history':[]})
        self.send_error(404)


def main():
    browser = browser_path()
    if not browser:
        raise RuntimeError('No supported browser found for the synthetic UI test')
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with TemporaryDirectory(prefix='nawa-browser-qa-') as temp:
            if not Path(temp).resolve().is_relative_to(Path(gettempdir()).resolve()):
                raise RuntimeError('Unexpected temporary browser directory')
            command = [browser, '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
                       '--user-data-dir=' + temp, '--virtual-time-budget=10000', '--dump-dom',
                       f'http://127.0.0.1:{server.server_port}/']
            result = subprocess.run(command, capture_output=True, text=True, timeout=45,
                                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            if result.returncode != 0 or 'data-synthetic-ui-check="PASS"' not in result.stdout:
                marker = re.search(r'data-synthetic-ui-error="([^"]*)"', result.stdout)
                detail = marker.group(1) if marker else 'no UI result'
                raise RuntimeError(f'Synthetic browser UI check did not pass (exit {result.returncode}; {detail})')
            print('PASS: real browser exercised synthetic intake UI with stubbed authentication and API.')
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


if __name__ == '__main__':
    main()

