<p align="center">
  <img src="banner.png" alt="yoytmusic-api banner" width="100%">
</p>

# 🎵 yoytmusic-api

[![Vercel Deployment](https://img.shields.io/badge/Vercel-black?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com/)
[![MIT License](https://img.shields.io/badge/License-MIT-orange?style=for-the-badge)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)

A professional, serverless HTTP wrapper for **ytmusicapi**. Specifically built for Vercel, it transforms the powerful Python library into a set of clean, CORS-ready JSON endpoints.

---

## 📚 Documentation & Explorer

This project comes with a built-in documentation suite to help you get started quickly:

- **[Interactive Playground](https://shubhamnpk.github.io/yoytmusic-api/docs/playground.html)**: Test every endpoint live from your browser.
- **[OpenAPI Reference](https://shubhamnpk.github.io/yoytmusic-api/docs/index.html)**: Full interactive Swagger-style documentation.
- **[OpenAPI Spec (JSON)](https://shubhamnpk.github.io/yoytmusic-api/docs/openapi.json)**: Import into Postman, Insomnia, or generate SDKs.

---

## ✨ Features

- 🏎️ **Serverless First**: Zero-config deployment on Vercel with Python serverless functions.
- 🔓 **Public Search**: Instant access to the YouTube Music catalog without needing API keys.
- 🛠️ **Generic Methods**: Access over 15+ `ytmusicapi` functions via a single structured endpoint.
- 🛰️ **CORS-Ready**: `Access-Control-Allow-Origin: *` enabled for direct frontend usage.
- 📦 **Minimal Footprint**: Lightweight dependencies and fast cold starts.

---

> [!NOTE]
> **API Root**: While the static documentation is hosted at the root of the project, the actual API endpoints are scoped under the `/api` path. If you visit the root of your API deployment (e.g., on Vercel) and see a 404, simply append `/api` to the URL to access the API entry point.

---
### 🏥 System Health
- **`GET /api/health`**
  - **Description**: Quick uptime check.
  - **Response**: `{"ok": true}`

- **`GET /api/version`**
  - **Description**: Returns version metadata for the app and `ytmusicapi`.

### 🔍 Search Catalog
- **`GET /api/public/search`**
  - **Parameters**:
    - `q` (required): Your search query.
    - `limit` (optional): `1` to `25` (default: 10).
    - `filter` (optional): `songs`, `videos`, `albums`, `artists`, `playlists`.
  - **Example**:
    ```bash
    curl "https://yoyt.vercel.app/api/public/search?q=Oasis&limit=5&filter=songs"
    ```

### ⚡ Generic Method Caller
Invoke any supported `ytmusicapi` method using either GET or POST.

- **`GET /api/public/ytmusic`**
  - **Params**: `method`, `args` (JSON array), `kwargs` (JSON object).
- **`POST /api/public/ytmusic`**
  ```json
  {
    "method": "get_album",
    "args": ["MPREb_00000000000"],
    "kwargs": {}
  }
  ```

#### ✅ Supported Allowlisted Methods:
`search`, `get_song`, `get_album`, `get_artist`, `get_artist_albums`, `get_artist_singles`, `get_artist_videos`, `get_artist_playlists`, `get_artist_related`, `get_playlist`, `get_watch_playlist`, `get_lyrics`, `get_home`, `get_explore`, `get_new_releases`, `get_charts`, `get_mood_categories`, `get_mood_playlists`.

---

## 🚀 Deployment (Vercel)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FShubhamnpk%2Fyoytmusic-api)

1. **Fork** this repository.
2. In your Vercel dashboard, click **"Add New Project"** and import the fork.
3. Vercel will automatically detect the Python functions in `api/` and the static files at the root.
4. Set the `data-repo` attribute on the `<body>` tag in `index.html` to point to your new repo.

---

## 🧑‍💻 Local Development

1. **Setup**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Run**:
   ```bash
   python dev_server.py
   ```
   - Dashboard: `http://localhost:3000`
   - API: `http://localhost:3000/api`
   - Docs: `http://localhost:3000/docs/index.html`

3. **Test**:
   ```bash
   pip install -r requirements-dev.txt
   pytest
   ```

---

## 🛡️ Security & CORS

- **CORS**: This API is bridge-configured for frontend usage. It allows all origins (`*`) by default.
- **Safety**: Only "read-only" methods are allowlisted for public endpoints. Methods that modify data (like `create_playlist`) require OAuth, which is currently stubbed in `/api/auth`.

---

## 📄 License & Contributing

Distributed under the **MIT License**. See [LICENSE](LICENSE) for more information. Contributions are welcome! Check [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

<p align="center">
  Built on the shoulders of giants: <a href="https://github.com/sigma67/ytmusicapi">ytmusicapi</a>.
</p>
