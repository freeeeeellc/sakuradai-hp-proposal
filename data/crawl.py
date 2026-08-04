import re, json, sys, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

BASE = "https://xn--6oqs1jd2v68dy45a.com/"
HOST = "xn--6oqs1jd2v68dy45a.com"
OLDHOST = "www.i-sakuradai.jp"

pages = {}      # url -> dict
queue = ["index.html"]
seen = set(queue)
assets = {}     # non-html internal (pdf etc) -> status
external = {}   # external link -> count

def norm(base, href):
    href = href.strip().replace("\\", "/")
    if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
        return None
    u = urllib.parse.urljoin(BASE + base, href)
    p = urllib.parse.urlsplit(u)
    if p.scheme not in ("http", "https"):
        return None
    if p.netloc in (HOST,):
        return ("int", p.path.lstrip("/") + (("?" + p.query) if p.query else ""))
    return ("ext", urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, p.query, "")))

def decode(data, headers):
    m = re.search(rb'charset\s*=\s*["\']?([\w\-]+)', data[:2000], re.I)
    dec = m.group(1).decode("ascii").lower() if m else None
    for enc in [dec, "utf-8", "cp932", "euc-jp"]:
        if not enc: continue
        try:
            e = {"shift_jis": "cp932", "shift-jis": "cp932", "sjis": "cp932", "x-sjis": "cp932"}.get(enc, enc)
            return data.decode(e), dec, e
        except Exception:
            continue
    return data.decode("utf-8", "replace"), dec, "utf-8?"

def fetch(path):
    url = BASE + path
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (site-audit)"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read(), int(r.headers.get("Content-Length") or 0)
    except urllib.error.HTTPError as e:
        return e.code, "", b"", 0
    except Exception as e:
        return -1, str(e), b"", 0

def head(url):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0 (site-audit)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return -1

HTMLEXT = (".html", ".htm", "/")

while queue:
    batch, queue = queue[:24], queue[24:]
    with ThreadPoolExecutor(16) as ex:
        results = list(ex.map(fetch, batch))
    for path, (status, ctype, data, _) in zip(batch, results):
        rec = {"path": path, "status": status, "size": len(data)}
        pages[path] = rec
        if status != 200 or "html" not in ctype.lower():
            rec["ctype"] = ctype
            continue
        text, declared, used = decode(data, ctype)
        rec["declared"] = declared
        rec["actual"] = used
        m = re.search(r"<title>(.*?)</title>", text, re.I | re.S)
        rec["title"] = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        rec["frameset"] = bool(re.search(r"<frameset", text, re.I))
        rec["generator"] = bool(re.search(r'GENERATOR"?\s*content="([^"]*)"', text, re.I))
        g = re.search(r'name="GENERATOR"\s+content="([^"]*)"', text, re.I)
        rec["gen"] = g.group(1) if g else ""
        rec["viewport"] = bool(re.search(r'name="viewport"', text, re.I))
        rec["desc"] = bool(re.search(r'name="description"', text, re.I))
        rec["h1"] = len(re.findall(r"<h1[\s>]", text, re.I))
        rec["oldlinks"] = len(re.findall(OLDHOST, text))
        links = re.findall(r'(?:href|src)\s*=\s*["\']([^"\'>]+)["\']', text, re.I)
        outs = []
        for h in links:
            n = norm(path, h)
            if not n: continue
            kind, u = n
            if kind == "ext":
                external[u] = external.get(u, 0) + 1
                continue
            low = u.lower().split("?")[0]
            if low.endswith((".html", ".htm")) or low.endswith("/"):
                outs.append(u)
                if u not in seen:
                    seen.add(u); queue.append(u)
            elif low.endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip")):
                assets[u] = None
        rec["out"] = sorted(set(outs))

json.dump({"pages": pages, "assets": sorted(assets), "external": external},
          open("crawl.json", "w"), ensure_ascii=False, indent=1)
print("pages crawled:", len(pages))
print("ok:", sum(1 for p in pages.values() if p["status"] == 200))
print("404/err:", sorted((p["path"], p["status"]) for p in pages.values() if p["status"] != 200)[:80])
print("docs/pdf found:", len(assets))
print("external hosts:", len(external))
