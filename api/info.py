import json
from http.server import BaseHTTPRequestHandler

from .version_info import get_version_payload


def _json_response(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(body)


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        payload = {
            "name": "yoytmusic-api",
            "status": "ok",
            "version": get_version_payload(),
            "endpoints": {
                "health": "/api/health",
                "version": "/api/version",
                "public_search": "/api/public/search",
                "public_method": "/api/public/ytmusic",
                "auth_method": "/api/auth/ytmusic",
                "openapi": "/docs/openapi.json",
            },
        }
        _json_response(self, 200, payload)
