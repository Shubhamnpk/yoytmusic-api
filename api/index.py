import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from ytmusicapi import YTMusic

from .version_info import get_version_payload
from .search import clamp_limit, execute_search, DEFAULT_LIMIT
from . import ytmusic as ytm


_ytmusic = YTMusic()


def _json_response(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
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


def _handle_info(h):
    _json_response(h, 200, {
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
    })


def _handle_search(h, params):
    query = (params.get("q") or [""])[0].strip()
    if not query:
        return _json_response(h, 400, {"error": "Missing required query param: q"})

    filter_param = (params.get("filter") or [None])[0]
    limit_raw = (params.get("limit") or [str(DEFAULT_LIMIT)])[0]
    try:
        limit = int(limit_raw)
    except ValueError:
        return _json_response(h, 400, {"error": "limit must be an integer"})

    limit = clamp_limit(limit)
    try:
        results = execute_search(_ytmusic, query, filter_param, limit)
    except Exception as exc:
        return _json_response(h, 500, {"error": "ytmusicapi search failed", "detail": str(exc)})

    _json_response(h, 200, {"query": query, "count": len(results), "items": results})


def _handle_ytmusic_get(h, params):
    method = (params.get("method") or [""])[0].strip()
    if not method:
        return _json_response(h, 400, {"error": "Missing required query param: method"})

    args_raw = (params.get("args") or [""])[0].strip()
    kwargs_raw = (params.get("kwargs") or [""])[0].strip()
    try:
        args = json.loads(args_raw) if args_raw else []
        kwargs = json.loads(kwargs_raw) if kwargs_raw else {}
    except json.JSONDecodeError:
        return _json_response(h, 400, {"error": "args/kwargs must be valid JSON"})

    if not isinstance(args, list) or not isinstance(kwargs, dict):
        return _json_response(h, 400, {"error": "args must be a list and kwargs must be an object"})

    try:
        result = ytm.call_method(_ytmusic, method, args, kwargs)
    except ValueError as exc:
        return _json_response(h, 400, {"error": str(exc), "allowed_methods": sorted(ytm.ALLOWED_METHODS)})
    except Exception as exc:
        return _json_response(h, 500, {"error": "ytmusicapi call failed", "detail": str(exc)})

    _json_response(h, 200, {"method": method, "result": result})


def _handle_ytmusic_post(h):
    body = _parse_body(h)
    if body is None:
        return _json_response(h, 400, {"error": "Invalid JSON body"})

    method = (body.get("method") or "").strip()
    if not method:
        return _json_response(h, 400, {"error": "Missing required field: method"})

    args = body.get("args", [])
    kwargs = body.get("kwargs", {})
    if not isinstance(args, list) or not isinstance(kwargs, dict):
        return _json_response(h, 400, {"error": "args must be a list and kwargs must be an object"})

    try:
        result = ytm.call_method(_ytmusic, method, args, kwargs)
    except ValueError as exc:
        return _json_response(h, 400, {"error": str(exc), "allowed_methods": sorted(ytm.ALLOWED_METHODS)})
    except Exception as exc:
        return _json_response(h, 500, {"error": "ytmusicapi call failed", "detail": str(exc)})

    _json_response(h, 200, {"method": method, "result": result})


def _handle_auth_stub(h):
    _json_response(h, 401, {
        "error": "Authentication required",
        "detail": "OAuth support is not enabled yet for this endpoint.",
        "auth_required": True,
    })


# Route table: path -> GET handler
_GET_ROUTES = {
    "/api":                 lambda h, p: _handle_info(h),
    "/api/":                lambda h, p: _handle_info(h),
    "/api/health":          lambda h, p: _json_response(h, 200, {"ok": True}),
    "/api/version":         lambda h, p: _json_response(h, 200, get_version_payload()),
    "/api/search":          lambda h, p: _handle_search(h, p),
    "/api/public/search":   lambda h, p: _handle_search(h, p),
    "/api/ytmusic":         lambda h, p: _handle_ytmusic_get(h, p),
    "/api/public/ytmusic":  lambda h, p: _handle_ytmusic_get(h, p),
    "/api/auth/ytmusic":    lambda h, p: _handle_auth_stub(h),
}

# Route table: path -> POST handler
_POST_ROUTES = {
    "/api/ytmusic":         lambda h: _handle_ytmusic_post(h),
    "/api/public/ytmusic":  lambda h: _handle_ytmusic_post(h),
    "/api/auth/ytmusic":    lambda h: _handle_auth_stub(h),
}


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if len(path) > 1:
            path = path.rstrip("/")
        params = parse_qs(parsed.query)

        route = _GET_ROUTES.get(path)
        if route:
            return route(self, params)

        # If not an API route, send 404 so Vercel can try static files
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        route = _POST_ROUTES.get(path)
        if route:
            return route(self)

        _json_response(self, 404, {"error": "Not found"})
