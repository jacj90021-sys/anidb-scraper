# Site: anidb.app (anidb-scraper)

A **captcha-free** aggregator — its API is not gated behind reCAPTCHA/Cloudflare.
Reached via `curl_cffi` browser-impersonation (the scraper uses it to dodge TLS
fingerprinting).

## Method notes
- No packed jwplayer, no Cloudflare wall on the API — closest to pure **M2/M6**.
- The lesson for the playbook: when a site blocks by **TLS fingerprint** (not
  JS challenge), use `curl_cffi` / browser-impersonation instead of plain `requests`.
  Plain curl/requests get 403; impersonation works.
- This is the "easy" end of the spectrum — capture the API contract (M6) and you're done.

## Why it matters in the playbook
anidb demonstrates that not every site needs M3 (node-decode) or M4 (self-resolve).
Match the anti-bot mechanism: fingerprint → impersonate; JS packer → node-decode;
mislabeled upstream → self-resolve. Don't over-engineer.

## Repo
`github.com/jacj90021-sys/anidb-scraper`
