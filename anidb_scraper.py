"""
anidb.app scraper — direct HLS, NO captcha, NO Cloudflare challenge (uses curl_cffi
browser-impersonation to pass Cloudflare's TLS check).

Live-verified flow (2026-08-02):
  /search/suggestions?q=         -> HTML w/ <a href="/anime/<slug>-<id>">
  /api/frontend/anime/<id>/episodes -> {"episodes":[{"id","number","filler"}]}
  /api/frontend/episode/<epId>/languages -> {"languages":[{code,name,embed_url}]}
  /embed/<embedId>               -> JWPlayer w/ master.m3u8 on hls.anidb.app
  master.m3u8                    -> real .ts segments (playable HLS)

Usage:
  python3 anidb_scraper.py search <query>
  python3 anidb_scraper.py episodes <animeId>
  python3 anidb_scraper.py stream <animeId> <epNumber>
"""
import sys, re, json, urllib.parse
from curl_cffi import requests as cffi

BASE = "https://anidb.app"

def _get(path, **kw):
    return cffi.get(BASE + path, impersonate="chrome", timeout=30, **kw)

def search(q):
    r = _get("/search/suggestions?q=" + urllib.parse.quote(q))
    links = re.findall(r'href="(https://anidb\.app/anime/[^"]+)"[^>]*>\s*<img[^>]+alt="([^"]+)"', r.text)
    out = []
    for href, name in links:
        m = re.search(r'/anime/([^/?#]+)$', href)
        slug = m.group(1) if m else href
        # numeric id is the trailing -NNNN
        mid = re.search(r'-(\d+)$', slug)
        out.append({"slug": slug, "id": mid.group(1) if mid else None, "name": name})
    return out

def episodes(anime_id):
    r = _get(f"/api/frontend/anime/{anime_id}/episodes")
    r.raise_for_status()
    return r.json().get("episodes", [])

def stream(anime_id, ep_number):
    eps = episodes(anime_id)
    ep = next((e for e in eps if str(e.get("number")) == str(ep_number)), None)
    if not ep:
        # fall back: ep list may use number2 or 0-index
        ep = eps[int(ep_number) - 1] if eps and ep_number.isdigit() else None
    if not ep:
        return {"error": f"episode {ep_number} not found (have {len(eps)} eps)"}
    r = _get(f"/api/frontend/episode/{ep['id']}/languages")
    r.raise_for_status()
    langs = r.json().get("languages", [])
    result = []
    for lg in langs:
        emb = lg["embed_url"].rstrip("/").split("/")[-1]
        er = _get(f"/embed/{emb}")
        m3 = re.search(r'(https?://hls\.anidb\.app/stream/[^"\'\s]+\.m3u8)', er.text)
        if m3:
            result.append({"lang": lg["code"], "name": lg["name"], "m3u8": m3.group(1)})
    return {"episode": ep, "streams": result}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "search":
        print(json.dumps(search(sys.argv[2]), ensure_ascii=False, indent=1))
    elif cmd == "episodes":
        print(json.dumps(episodes(sys.argv[2]), ensure_ascii=False, indent=1))
    elif cmd == "stream":
        print(json.dumps(stream(sys.argv[2], sys.argv[3]), ensure_ascii=False, indent=1))
    else:
        print("unknown cmd:", cmd)
