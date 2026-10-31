#!/usr/bin/env python3
"""Fetch a static page through the session proxy and print readable text.

Use for pages that do not need JavaScript: airline route pages, review/forum threads,
government travel advice, articles. For flight/hotel result pages use browse.js.

Why curl: the WebFetch tool resolves DNS itself and does not use the session proxy, so
it fails on allowed hosts. curl honours HTTPS_PROXY and the proxy CA bundle.

Usage: fetch_static.py <url> [--max 6000] [--prices]
Prints JSON: {url, status, title, text|priceLines, jsonld}. Embedded JSON-LD (schema.org
offers, ratings) is included because it often holds prices even when the page text doesn't.
"""
import argparse, html, json, re, subprocess, sys

PRICE = re.compile(r"(£|€|\$|\b(?:GBP|EUR|USD)\b)\s?\d|\d[\d,\.]*\s?(£|€|\b(?:GBP|EUR|USD)\b)")
BOT = re.compile(r"captcha|are you a robot|verify you are human|unusual traffic|access denied", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url"); ap.add_argument("--max", type=int, default=6000)
    ap.add_argument("--prices", action="store_true")
    a = ap.parse_args()
    cmd = ["curl", "-sS", "-L", "--compressed", "--max-time", "25", "--max-filesize", "8000000",
           "-A", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
           "-H", "Accept-Language: en-GB,en;q=0.9", "-w", "\n%{http_code}", a.url]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = {"url": a.url}
    if r.returncode != 0:
        out["error"] = (r.stderr or "curl failed").strip().splitlines()[-1]
        print(json.dumps(out, indent=2)); sys.exit(1)
    body, _, status = r.stdout.rpartition("\n")
    out["status"] = int(status) if status.isdigit() else status
    m = re.search(r"<title[^>]*>(.*?)</title>", body, re.S | re.I)
    out["title"] = html.unescape(m.group(1)).strip() if m else None
    ld = []
    for blk in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', body, re.S | re.I):
        try:
            ld.append(json.loads(blk))
        except Exception:
            pass
    def slim(x):  # drop bulky fields that carry no prices or ratings
        if isinstance(x, dict):
            return {k: slim(v) for k, v in x.items() if k not in ("articleBody", "image", "logo", "publisher", "about")}
        if isinstance(x, list):
            return [slim(v) for v in x]
        return x
    if ld:
        s = json.dumps(slim(ld), ensure_ascii=False)
        out["jsonld"] = s[:4000] + ("..." if len(s) > 4000 else "")
    txt = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", body, flags=re.S | re.I)
    txt = re.sub(r"<(br|/p|/div|/li|/tr|/h\d)[^>]*>", "\n", txt, flags=re.I)
    txt = html.unescape(re.sub(r"<[^>]+>", " ", txt))
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r"\n\s*\n+", "\n", txt).strip()
    out["blocked"] = bool(BOT.search(txt[:3000])) or out["status"] in (403, 429)
    if a.prices:
        lines = txt.split("\n")
        out["priceLines"] = [l.strip() for l in lines if PRICE.search(l)][:100]
        if not out["priceLines"]:
            out["note"] = "no prices in static HTML; the page probably needs JavaScript, try browse.js"
    else:
        out["text"] = txt[: a.max]
        out["truncated"] = len(txt) > a.max
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # report as JSON so a bad page never aborts the whole search
        print(json.dumps({"url": sys.argv[1] if len(sys.argv) > 1 else None,
                          "error": f"{type(e).__name__}: {e}"}, indent=2))
        sys.exit(1)
