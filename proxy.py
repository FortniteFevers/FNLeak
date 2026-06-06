#!/usr/bin/env python3
"""
Local CORS proxy for football-data.org
Forwards requests to https://api.football-data.org/v4
and adds Access-Control-Allow-Origin: * so the browser can call it.
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.error
import urllib.parse
import json
import os
import ssl

# macOS Python often lacks bundled certs — use unverified context for this trusted endpoint
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

API_BASE = 'https://api.football-data.org/v4'


class ProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress request logs

    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'X-Auth-Token, Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        api_key = self.headers.get('X-Auth-Token', '')
        target  = f'{API_BASE}{self.path}'

        req = urllib.request.Request(
            target,
            headers={
                'X-Auth-Token':  api_key,
                'User-Agent':    'WC2026-FanSite/1.0',
                'Accept':        'application/json',
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as resp:
                body = resp.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self._cors_headers()
                self.end_headers()
                self.wfile.write(body)

        except urllib.error.HTTPError as e:
            body = e.read()
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self._cors_headers()
            self.end_headers()
            self.wfile.write(body)

        except Exception as e:
            body = json.dumps({'error': str(e)}).encode()
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self._cors_headers()
            self.end_headers()
            self.wfile.write(body)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8003))
    server = HTTPServer(('', port), ProxyHandler)
    print(f'✓ Proxy running on :{port}  →  {API_BASE}')
    server.serve_forever()
