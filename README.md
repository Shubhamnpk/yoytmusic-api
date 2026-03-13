# yoytmusic-api

![yoytmusic-api favicon](public/favicon.svg)

**yoytmusic-api**
serverless HTTP wrapper for `ytmusicapi` with public endpoints, OpenAPI docs, and a testing playground. Serverless HTTP wrapper around `ytmusicapi` for public YouTube Music data. Designed for Vercel, with CORS enabled and a minimal surface area for quick integrations.

## Features

- Public, read-only YouTube Music data over HTTP.
- Explicit public/auth endpoint split for future OAuth support.
- Generic method endpoint for supported `ytmusicapi` methods.
- Serverless-friendly limits and predictable responses.
- Static landing page at `/` and docs at `/docs/`.
- OpenAPI spec at `/docs/openapi.json`.
- Custom favicon at `/favicon.svg`.

## Docs Pages

- Landing: `/`
- Docs: `/docs/`
- OpenAPI: `/docs/openapi.json`

## Quick Start (Vercel)

1. Push this repo to GitHub.
2. Create a new Vercel project and import the repo.
3. Deploy.

After deploy, your endpoints are live at `https://YOUR_APP.vercel.app/api/...`.

To make the landing page deploy button work, set your repo URL in `index.html` by updating `data-repo` on the `<body>` tag.

## Local Development

1. Install runtime deps.

```bash
pip install -r requirements.txt
```

2. Run the local dev server (no Vercel login required).

```bash
python dev_server.py
```

The landing page is served at `http://localhost:3000` and the API is under `/api/`.

If you want to emulate Vercel's serverless runtime locally, you can still use `vercel dev` (requires `vercel login`).

## Endpoint Reference

### `GET /api/health`

Response:

```json
{"ok": true}
```

### `GET /api/version`

Response:

```json
{"app_version": "0.1.0", "ytmusicapi_version": "X.Y.Z", "build_time": "2026-03-12T00:00:00Z"}
```

`build_time` is populated from the `BUILD_TIME` env var (ISO-8601 string). `app_version` defaults to `0.1.0` but can be overridden with `APP_VERSION`.

### `GET /api/search`

Query parameters:

| Name | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `q` | string | Yes | - | Search query |
| `limit` | int | No | 10 | Clamped between 1 and 25 |
| `filter` | string | No | null | `songs`, `videos`, `albums`, `artists`, `playlists` |

Response:

```json
{
  "query": "Oasis",
  "count": 5,
  "items": [
    {"title": "..."}
  ]
}
```

### `GET /api/public/search`

Same behavior as `/api/search`, but explicitly scoped to public access. Recommended for new clients.

### `GET /api/public/global-search`

Global search that combines multiple categories (songs + artists + playlists by default).

Query parameters:

| Name | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `q` | string | Yes | - | Search query |
| `limit` | int | No | 10 | Clamped between 1 and 25 |
| `filters` | string | No | `songs,artists,playlists` | Comma-separated list of `songs`, `videos`, `albums`, `artists`, `playlists` |

### `GET /api/ytmusic`

Query parameters:

| Name | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `method` | string | Yes | - | Must be in allowlist |
| `args` | JSON array | No | `[]` | Positional args for method |
| `kwargs` | JSON object | No | `{}` | Keyword args for method |

Example:

```bash
curl "https://YOUR_APP.vercel.app/api/ytmusic?method=get_playlist&args=[\"PLAYLIST_ID\"]"
```

### `POST /api/ytmusic`

JSON body:

```json
{
  "method": "get_song",
  "args": ["VIDEO_ID"],
  "kwargs": {}
}
```

Response:

```json
{
  "method": "get_song",
  "result": {"videoId": "VIDEO_ID"}
}
```

### `GET /api/public/ytmusic`

Same behavior as `/api/ytmusic`, but explicitly scoped to public access. Recommended for new clients.

### `POST /api/public/ytmusic`

Same behavior as `/api/ytmusic`, but explicitly scoped to public access. Recommended for new clients.

### `GET /api/auth/ytmusic`

Reserved for OAuth-protected methods. Returns `401` until OAuth is enabled.

### `POST /api/auth/ytmusic`

Reserved for OAuth-protected methods. Returns `401` until OAuth is enabled.

## Allowed Methods (No Auth)

- `search`
- `get_song`
- `get_album`
- `get_artist`
- `get_artist_albums`
- `get_artist_singles`
- `get_artist_videos`
- `get_artist_playlists`
- `get_artist_related`
- `get_playlist`
- `get_watch_playlist`
- `get_lyrics`
- `get_home`
- `get_explore`
- `get_new_releases`
- `get_charts`
- `get_mood_categories`
- `get_mood_playlists`

## Error Format

```json
{
  "error": "...",
  "detail": "...",
  "allowed_methods": ["..."]
}
```

## CORS

This API sets:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, POST, OPTIONS`

## Tests

1. Install dev deps.

```bash
pip install -r requirements-dev.txt
```

2. Run tests.

```bash
pytest
```

## Limitations

- Unauthenticated only. Library, playlists management, and uploads require OAuth.
- Results depend on `ytmusicapi` behavior and YouTube Music availability.

## Roadmap

- OAuth support with per-user tokens.
- Optional API key protection.
- More examples and SDK snippets.
