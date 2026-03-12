import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from ytmusicapi import YTMusic


_ytmusic = YTMusic()

# Read-only, public methods that do NOT require authentication.
# If ytmusicapi changes, unsupported methods will be rejected at runtime.
ALLOWED_METHODS = {
    "search",
    "get_song",
    "get_album",
    "get_artist",
    "get_artist_albums",
    "get_artist_singles",
    "get_artist_videos",
    "get_artist_playlists",
    "get_artist_related",
    "get_playlist",
    "get_watch_playlist",
    "get_lyrics",
    "get_home",
    "get_explore",
    "get_new_releases",
    "get_charts",
    "get_mood_categories",
    "get_mood_playlists",
}


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


def _method_not_allowed(handler, message):
    _json_response(handler, 400, {"error": message, "allowed_methods": sorted(ALLOWED_METHODS)})


def validate_method(ytmusic, method):
    if not method:
        return "Missing required method"
    if method not in ALLOWED_METHODS:
        return "Method is not allowed without auth"
    if not hasattr(ytmusic, method):
        return "Method not supported by installed ytmusicapi"
    return None


def call_method(ytmusic, method, args, kwargs):
    error = validate_method(ytmusic, method)
    if error:
        raise ValueError(error)
    return getattr(ytmusic, method)(*args, **kwargs)


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        method = (params.get("method") or [""])[0].strip()
        error = validate_method(_ytmusic, method)
        if error:
            return _method_not_allowed(self, error.replace("Missing required method", "Missing required query param: method"))

        # Accept args as JSON in a single query param for GET convenience.
        # Example: /api/ytmusic?method=get_song&args=["VIDEO_ID"]
        args_raw = (params.get("args") or [""])[0].strip()
        kwargs_raw = (params.get("kwargs") or [""])[0].strip()
        try:
            args = json.loads(args_raw) if args_raw else []
            kwargs = json.loads(kwargs_raw) if kwargs_raw else {}
        except json.JSONDecodeError:
            return _json_response(self, 400, {"error": "args/kwargs must be valid JSON"})

        if not isinstance(args, list) or not isinstance(kwargs, dict):
            return _json_response(self, 400, {"error": "args must be a list and kwargs must be an object"})

        try:
            result = call_method(_ytmusic, method, args, kwargs)
        except ValueError as exc:
            return _method_not_allowed(self, str(exc))
        except Exception as exc:
            return _json_response(self, 500, {"error": "ytmusicapi call failed", "detail": str(exc)})

        _json_response(self, 200, {"method": method, "result": result})

    def do_POST(self):
        body = _parse_body(self)
        if body is None:
            return _json_response(self, 400, {"error": "Invalid JSON body"})

        method = (body.get("method") or "").strip()
        error = validate_method(_ytmusic, method)
        if error:
            return _method_not_allowed(self, error.replace("Missing required method", "Missing required field: method"))

        args = body.get("args", [])
        kwargs = body.get("kwargs", {})
        if not isinstance(args, list) or not isinstance(kwargs, dict):
            return _json_response(self, 400, {"error": "args must be a list and kwargs must be an object"})

        try:
            result = call_method(_ytmusic, method, args, kwargs)
        except ValueError as exc:
            return _method_not_allowed(self, str(exc))
        except Exception as exc:
            return _json_response(self, 500, {"error": "ytmusicapi call failed", "detail": str(exc)})

        _json_response(self, 200, {"method": method, "result": result})
