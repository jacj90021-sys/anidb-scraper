# anidb-scraper

A clean, **captcha-free** anime streaming scraper for [anidb.app](https://anidb.app).

> **📚 Scraping method playbook:** this repo also documents the general A→Z
> techniques for scraping anime streams. See [`docs/`](docs/):
> - [`docs/METHODS.md`](docs/METHODS.md) — 8 site-agnostic methods (M1–M8)
> - [`docs/sites/`](docs/sites/) — per-site writeups (anidb, anikage, just4anime, otakuhg, animegg, megaplay, vivibebe)
> - [`docs/just4anime_PROOF.md`](docs/just4anime_PROOF.md) — live-verified proof all 6 just4anime servers work
> - [`docs/templates/`](docs/templates/) — reusable code (node packer decoder, HLS verify, Flask API)
> - [`docs/pitfalls.md`](docs/pitfalls.md) — the mistakes that cost the most time
> - [`docs/methods.json`](docs/methods.json) — machine-readable index

Unlike AllAnime-based scrapers, anidb.app does **not** gate its API behind a
reCAPTCHA or Cloudflare challenge (it is reached via `curl_cffi` browser
impersonation to pass Cloudflare's TLS check). Every episode resolves to a
**direct HLS `.m3u8`** hosted on `hls.anidb.app` — no third-party provider
hoops, no signing, no captcha.

## How it works (live-verified)

```
/search/suggestions?q=                  -> anime list (/anime/<slug>-<id>)
/api/frontend/anime/<id>/episodes       -> {"episodes":[{id,number,filler}]}
/api/frontend/episode/<epId>/languages  -> {"languages":[{code,name,embed_url}]}
/embed/<embedId>                        -> JWPlayer w/ hls.anidb.app master.m3u8
master.m3u8                             -> real .ts segments (playable HLS)
```

Each episode exposes **2 audio streams**:
- `eng` — English
- `jpn` — Japanese

Both return a direct `https://hls.anidb.app/stream/.../master.m3u8`.

## Install

```bash
pip install curl_cffi
```

## Usage

```bash
python3 anidb_scraper.py search <query>
python3 anidb_scraper.py episodes <animeId>
python3 anidb_scraper.py stream <animeId> <episodeNumber>
```

### Examples

```bash
$ python3 anidb_scraper.py search naruto
[
  {
    "slug": "naruto-3686",
    "id": "3686",
    "name": "Naruto"
  },
  ...
]

$ python3 anidb_scraper.py episodes 3686
# 220 episodes ...

$ python3 anidb_scraper.py stream 3686 1
{
  "episode": {"id": 70219, "number": 1, "filler": false},
  "streams": [
    {"lang": "eng", "name": "English",  "m3u8": "https://hls.anidb.app/stream/.../master.m3u8"},
    {"lang": "jpn", "name": "Japanese", "m3u8": "https://hls.anidb.app/stream/.../master.m3u8"}
  ]
}
```

The `m3u8` URLs are playable directly in any HLS player (hls.js, VLC, mpv, etc.).

## Notes

- `animeId` is the numeric suffix in the anime URL, e.g. `naruto-3686` -> `3686`.
- Cloudflare is bypassed via `curl_cffi` Chrome impersonation; if anidb.app
  tightens protection you may need to rotate the impersonation profile.
- This is a single-source scraper. It is intentionally simple and dependency-light.
