import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from ytmusicapi import YTMusic

from api.search import clamp_limit, DEFAULT_LIMIT, MAX_LIMIT


DEFAULT_FILTERS = ["songs", "artists", "playlists"]
ALLOWED_FILTERS = {"songs", "videos", "albums", "artists", "playlists"}

# Reuse a single client across invocations when possible.
_ytmusic = YTMusic()


def _split_limit(total, buckets):
    base = total // buckets
    remainder = total % buckets
    return [base + (1 if i < remainder else 0) for i in range(buckets)]


def _result_key(item):
    for key in ("videoId", "playlistId", "browseId"):
        value = item.get(key)
        if value:
            return f"{key}:{value}"
    title = item.get("title") or item.get("name")
    if title:
        return f"title:{title}"
    return json.dumps(item, sort_keys=True, ensure_ascii=False)


def _parse_filters(raw_filters):
    if raw_filters is None:
        return list(DEFAULT_FILTERS)
    raw_filters = raw_filters.strip()
    if not raw_filters:
        return None
    filters = [value.strip() for value in raw_filters.split(",") if value.strip()]
    if not filters:
        return None
    invalid = [value for value in filters if value not in ALLOWED_FILTERS]
    if invalid:
        raise ValueError(f"Invalid filters: {', '.join(sorted(invalid))}")
    return filters


def execute_global_search(ytmusic, query, filters, limit):
    per_limits = _split_limit(limit, len(filters))
    combined = []
    for filter_value, per_limit in zip(filters, per_limits):
        if per_limit <= 0:
            continue
        combined.extend(ytmusic.search(query, filter=filter_value, limit=per_limit))

    seen = set()
    deduped = []
    for item in combined:
        key = _result_key(item)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


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

        limit_raw = (params.get("limit") or [str(DEFAULT_LIMIT)])[0]
        try:
            limit = int(limit_raw)
        except ValueError:
            return _json_response(self, 400, {"error": "limit must be an integer"})

        limit = clamp_limit(limit, max_value=MAX_LIMIT)

        filters_raw = (params.get("filters") or [None])[0]
        try:
            filters = _parse_filters(filters_raw)
        except ValueError as exc:
            return _json_response(self, 400, {"error": str(exc)})

        if not filters:
            return _json_response(
                self,
                400,
                {"error": "filters must be a comma-separated list of allowed values"},
            )

        try:
            results = execute_global_search(_ytmusic, query, filters, limit)
        except Exception as exc:
            return _json_response(self, 500, {"error": "ytmusicapi search failed", "detail": str(exc)})

        _json_response(
            self,
            200,
            {"query": query, "count": len(results), "items": results, "filters": filters},
        )
