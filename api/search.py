import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from ytmusicapi import YTMusic


DEFAULT_LIMIT = 10
MAX_LIMIT = 25

# Reuse a single client across invocations when possible.
_ytmusic = YTMusic()


def clamp_limit(value, min_value=1, max_value=MAX_LIMIT):
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value


def execute_search(ytmusic, query, filter_param, limit):
    return ytmusic.search(query, filter=filter_param, limit=limit)


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
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        query = (params.get("q") or [""])[0].strip()
        if not query:
            return _json_response(self, 400, {"error": "Missing required query param: q"})

        filter_param = (params.get("filter") or [None])[0]
        limit_raw = (params.get("limit") or [str(DEFAULT_LIMIT)])[0]
        try:
            limit = int(limit_raw)
        except ValueError:
            return _json_response(self, 400, {"error": "limit must be an integer"})

        # Keep responses small and predictable for serverless limits.
        limit = clamp_limit(limit)

        try:
            results = execute_search(_ytmusic, query, filter_param, limit)
        except Exception as exc:
            return _json_response(self, 500, {"error": "ytmusicapi search failed", "detail": str(exc)})

        _json_response(self, 200, {"query": query, "count": len(results), "items": results})
