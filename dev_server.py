import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from ytmusicapi import YTMusic

from api.search import clamp_limit, execute_search, DEFAULT_LIMIT
from api import ytmusic as ytm
from api.version_info import get_version_payload


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

_ytmusic = YTMusic()


def _read_file(path):
    with open(path, "rb") as handle:
        return handle.read()


def _send_json(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(body)


def _send_html(handler, status, payload):
    handler.send_response(status)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


def _send_bytes(handler, status, payload, content_type):
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


def _send_text(handler, status, payload):
    body = payload.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/plain; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _parse_body(handler):
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


class RouterHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            return _send_html(self, 200, _read_file(os.path.join(ROOT_DIR, "index.html")))

        if path == "/favicon.svg":
            return _send_bytes(
                self,
                200,
                _read_file(os.path.join(ROOT_DIR, "favicon.svg")),
                "image/svg+xml; charset=utf-8",
            )

        if path in ("/docs", "/docs/"):
            return _send_html(self, 200, _read_file(os.path.join(ROOT_DIR, "docs", "index.html")))

        if path in ("/docs/playground", "/docs/playground.html"):
            return _send_html(self, 200, _read_file(os.path.join(ROOT_DIR, "docs", "playground.html")))

        if path == "/docs/openapi.json":
            return _send_bytes(
                self,
                200,
                _read_file(os.path.join(ROOT_DIR, "docs", "openapi.json")),
                "application/json; charset=utf-8",
            )

        if path == "/api/health":
            return _send_json(self, 200, {"ok": True})

        if path == "/api/version":
            return _send_json(self, 200, get_version_payload())

        if path in ("/api/search", "/api/public/search"):
            params = parse_qs(parsed.query)
            query = (params.get("q") or [""])[0].strip()
            if not query:
                return _send_json(self, 400, {"error": "Missing required query param: q"})

            filter_param = (params.get("filter") or [None])[0]
            limit_raw = (params.get("limit") or [str(DEFAULT_LIMIT)])[0]
            try:
                limit = int(limit_raw)
            except ValueError:
                return _send_json(self, 400, {"error": "limit must be an integer"})

            limit = clamp_limit(limit)
            try:
                results = execute_search(_ytmusic, query, filter_param, limit)
            except Exception as exc:
                return _send_json(self, 500, {"error": "ytmusicapi search failed", "detail": str(exc)})

            return _send_json(self, 200, {"query": query, "count": len(results), "items": results})

        if path in ("/api/ytmusic", "/api/public/ytmusic"):
            params = parse_qs(parsed.query)
            method = (params.get("method") or [""])[0].strip()
            if not method:
                return _send_json(self, 400, {"error": "Missing required query param: method"})

            args_raw = (params.get("args") or [""])[0].strip()
            kwargs_raw = (params.get("kwargs") or [""])[0].strip()
            try:
                args = json.loads(args_raw) if args_raw else []
                kwargs = json.loads(kwargs_raw) if kwargs_raw else {}
            except json.JSONDecodeError:
                return _send_json(self, 400, {"error": "args/kwargs must be valid JSON"})

            if not isinstance(args, list) or not isinstance(kwargs, dict):
                return _send_json(self, 400, {"error": "args must be a list and kwargs must be an object"})

            try:
                result = ytm.call_method(_ytmusic, method, args, kwargs)
            except ValueError as exc:
                return _send_json(self, 400, {"error": str(exc), "allowed_methods": sorted(ytm.ALLOWED_METHODS)})
            except Exception as exc:
                return _send_json(self, 500, {"error": "ytmusicapi call failed", "detail": str(exc)})

            return _send_json(self, 200, {"method": method, "result": result})

        if path == "/api/auth/ytmusic":
            return _send_json(
                self,
                401,
                {
                    "error": "Authentication required",
                    "detail": "OAuth support is not enabled yet for this endpoint.",
                    "auth_required": True,
                },
            )

        return _send_text(self, 404, "Not found")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path not in ("/api/ytmusic", "/api/public/ytmusic", "/api/auth/ytmusic"):
            return _send_text(self, 404, "Not found")

        if parsed.path == "/api/auth/ytmusic":
            return _send_json(
                self,
                401,
                {
                    "error": "Authentication required",
                    "detail": "OAuth support is not enabled yet for this endpoint.",
                    "auth_required": True,
                },
            )

        body = _parse_body(self)
        if body is None:
            return _send_json(self, 400, {"error": "Invalid JSON body"})

        method = (body.get("method") or "").strip()
        if not method:
            return _send_json(self, 400, {"error": "Missing required field: method"})

        args = body.get("args", [])
        kwargs = body.get("kwargs", {})
        if not isinstance(args, list) or not isinstance(kwargs, dict):
            return _send_json(self, 400, {"error": "args must be a list and kwargs must be an object"})

        try:
            result = ytm.call_method(_ytmusic, method, args, kwargs)
        except ValueError as exc:
            return _send_json(self, 400, {"error": str(exc), "allowed_methods": sorted(ytm.ALLOWED_METHODS)})
        except Exception as exc:
            return _send_json(self, 500, {"error": "ytmusicapi call failed", "detail": str(exc)})

        return _send_json(self, 200, {"method": method, "result": result})


def main():
    port = int(os.environ.get("PORT", "3000"))
    server = HTTPServer(("0.0.0.0", port), RouterHandler)
    print(f"Local server running on http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
