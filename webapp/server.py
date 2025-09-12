#!/usr/bin/env python3
import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


ANNOTATIONS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'annotations.json')


class Handler(SimpleHTTPRequestHandler):
    def _send_json(self, payload, status=200):
        data = json.dumps(payload).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/api/annotations':
            try:
                if os.path.exists(ANNOTATIONS_FILE):
                    with open(ANNOTATIONS_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    data = {"categories": [], "annotations": {}}
                self._send_json(data)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/annotations':
            try:
                length = int(self.headers.get('Content-Length', '0'))
                raw = self.rfile.read(length)
                payload = json.loads(raw.decode('utf-8') or '{}')
                # basic shape validation
                categories = payload.get('categories', [])
                annotations = payload.get('annotations', {})
                out = {"categories": categories, "annotations": annotations}
                with open(ANNOTATIONS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(out, f, ensure_ascii=False, indent=2)
                self._send_json({"ok": True})
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
        else:
            self.send_error(404, 'Not Found')


def main():
    addr = ('127.0.0.1', 5173)
    httpd = ThreadingHTTPServer(addr, Handler)
    print(f'Serving on http://{addr[0]}:{addr[1]} (save file: {ANNOTATIONS_FILE})')
    httpd.serve_forever()


if __name__ == '__main__':
    main()


