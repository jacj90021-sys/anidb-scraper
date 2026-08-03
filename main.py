"""
anidb.app FastAPI backend — captcha-free, direct HLS.
Deploy-ready for Render (Option A: backend-for-frontend for the Kotlin app).

Endpoints:
  GET /api/health
  GET /api/search?q=naruto
  GET /api/episodes?animeId=3686
  GET /api/sources?animeId=3686&ep=1   -> {episode, servers:[{server,name,m3u8,format}]}
"""
import re
import urllib.parse
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from curl_cffi import requests as cffi

BASE = "https://anidb.app"
app = FastAPI(title="anidb-scraper API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get(path):
    # Chrome impersonation to pass Cloudflare TLS check
    return cffi.get(BASE + path, impersonate="chrome", timeout=30)


@app.get("/api/health")
async def health():
    return {"status": "ok", "backend": "anidb.app", "cloudflare_bypass": "curl_cffi"}


@app.get("/api/search")
async def search(q: str):
    r = _get("/search/suggestions?q=" + urllib.parse.quote(q))
    out = []
    for href, name in re.findall(
        r'href="(https://anidb\.app/anime/[^"]+)"[^>]*>\s*<img[^>]+alt="([^"]+)"', r.text
    ):
        slug = href.rstrip("/").split("/")[-1]
        mid = re.search(r"-(\d+)$", slug)
        out.append({"slug": slug, "id": mid.group(1) if mid else None, "name": name})
    return {"results": out}


@app.get("/api/episodes")
async def episodes(animeId: str):
    r = _get(f"/api/frontend/anime/{animeId}/episodes")
    r.raise_for_status()
    return {"episodes": r.json().get("episodes", [])}


@app.get("/api/sources")
async def sources(animeId: str, ep: str):
    eps = _get(f"/api/frontend/anime/{animeId}/episodes").json().get("episodes", [])
    ep_obj = next((e for e in eps if str(e.get("number")) == str(ep)), None)
    if not ep_obj and ep.isdigit() and eps:
        idx = int(ep) - 1
        ep_obj = eps[idx] if 0 <= idx < len(eps) else None
    if not ep_obj:
        return {"error": f"episode {ep} not found", "servers": []}

    r = _get(f"/api/frontend/episode/{ep_obj['id']}/languages")
    r.raise_for_status()
    langs = r.json().get("languages", [])

    servers = []
    for lg in langs:
        embed_id = lg["embed_url"].rstrip("/").split("/")[-1]
        er = _get(f"/embed/{embed_id}")
        m3 = re.search(r"(https?://hls\.anidb\.app/stream/[^\"'\s]+\.m3u8)", er.text)
        if m3:
            servers.append(
                {
                    "server": lg["code"],   # eng / jpn
                    "name": lg["name"],     # English / Japanese
                    "m3u8": m3.group(1),
                    "format": "hls",
                }
            )
    return {"episode": ep_obj, "servers": servers}
