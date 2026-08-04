"""成果物一式を GitHub Pages 用の公開ツリー ../_site/ に組み立てる。
使い方: cd _audit && python3 gen_site.py
既存ファイルの削除は行わず、上書きコピーのみ。
"""
import re, html, shutil, pathlib

SRC = pathlib.Path(__file__).resolve().parent.parent      # さくらサービス/
OUT = SRC / "_site"
NOINDEX = '<meta name="robots" content="noindex,nofollow,noarchive">'

(OUT / "mockup").mkdir(parents=True, exist_ok=True)
(OUT / "data").mkdir(parents=True, exist_ok=True)

# ---------- 1. そのまま公開するファイル ----------
COPIES = [
    ("提案書_総合.html",             "proposal.html"),
    ("提案書_A4.html",               "proposal-a4.html"),
    ("提案書_A4.pdf",                "proposal-a4.pdf"),
    ("04_ページ一覧.html",            "pages.html"),
    ("mockup/index.html",            "mockup/index.html"),
    ("mockup/comparison.html",       "mockup/comparison.html"),
    ("mockup/preview-desktop.png",   "mockup/preview-desktop.png"),
    ("mockup/preview-comparison.png","mockup/preview-comparison.png"),
]
for s, d in COPIES:
    shutil.copy2(SRC / s, OUT / d)

DOCS = [
    ("01_サイトマップ.md",                    "sitemap.html",     "現状のサイトマップ"),
    ("02_改善提案.md",                        "improvements.html", "改善提案"),
    ("03_さくらサービスセンター連携設計.md",     "partnership.html",  "さくらサービスセンター連携設計"),
    ("CLAUDE.md",                             "notes.html",        "案件メモ"),
]
for s, _, _ in DOCS:
    shutil.copy2(SRC / s, OUT / "data" / s)
for f in ["crawl.py", "gen_list.py", "gen_site.py", "crawl.json", "lastmod.json", "full_list.md"]:
    shutil.copy2(SRC / "_audit" / f, OUT / "data" / f)


# ---------- 2. Markdown → HTML ----------
def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', t)
    return t


def md2html(md):
    lines, out, i = md.split("\n"), [], 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            i += 1; buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(html.escape(lines[i], quote=False)); i += 1
            i += 1
            out.append("<pre><code>" + "\n".join(buf) + "</code></pre>"); continue
        if re.match(r'^\|.*\|\s*$', ln) and i + 1 < len(lines) and re.match(r'^\|[\s:\-|]+\|\s*$', lines[i + 1]):
            def cells(r): return [c.strip() for c in r.strip().strip("|").split("|")]
            head = cells(ln); i += 2; body = []
            while i < len(lines) and re.match(r'^\|.*\|\s*$', lines[i]):
                body.append(cells(lines[i])); i += 1
            t = ["<div class='tw'><table><thead><tr>"]
            t += [f"<th>{inline(c)}</th>" for c in head]
            t.append("</tr></thead><tbody>")
            for r in body:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t)); continue
        m = re.match(r'^(#{1,6})\s+(.*)$', ln)
        if m:
            lv = len(m.group(1)); out.append(f"<h{lv}>{inline(m.group(2))}</h{lv}>"); i += 1; continue
        if re.match(r'^\s*---+\s*$', ln):
            out.append("<hr>"); i += 1; continue
        if re.match(r'^\s*[-*]\s+', ln) or re.match(r'^\s*\d+\.\s+', ln):
            tag = "ol" if re.match(r'^\s*\d+\.\s+', ln) else "ul"
            items = []
            while i < len(lines) and (re.match(r'^\s*[-*]\s+', lines[i]) or re.match(r'^\s*\d+\.\s+', lines[i])):
                items.append(re.sub(r'^\s*(?:[-*]|\d+\.)\s+', '', lines[i])); i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>"); continue
        if ln.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip("> ")); i += 1
            out.append("<blockquote>" + inline(" ".join(buf)) + "</blockquote>"); continue
        if ln.strip() == "":
            i += 1; continue
        buf = []
        while i < len(lines) and lines[i].strip() and \
                not re.match(r'^(#{1,6}\s|```|\||\s*[-*]\s|\s*\d+\.\s|>)', lines[i]) and \
                not re.match(r'^\s*---+\s*$', lines[i]):
            buf.append(lines[i]); i += 1
        if buf:
            out.append("<p>" + "<br>".join(inline(b) for b in buf) + "</p>")
    return "\n".join(out)


CSS = """
:root{--green:#1F4B3F;--sakura:#C4506E;--ink:#1D2226;--muted:#5A646D;--line:#E2E6E8}
*{box-sizing:border-box;margin:0;padding:0}
body{background:#EFF2F1;color:var(--ink);line-height:1.9;font-size:16px;
 font-family:"Hiragino Kaku Gothic ProN","Hiragino Sans","Yu Gothic Medium","Yu Gothic",Meiryo,sans-serif;-webkit-text-size-adjust:100%}
.sheet{max-width:900px;margin:0 auto;background:#fff;padding:34px 40px 60px;box-shadow:0 2px 30px rgba(20,40,30,.08);min-height:100vh}
.back{display:inline-block;margin-bottom:22px;font-size:.88rem;color:var(--green);text-decoration:none;font-weight:700}
.back:hover{text-decoration:underline}
h1{font-size:1.62rem;color:var(--green);letter-spacing:.03em;line-height:1.45;margin:0 0 18px;padding-bottom:12px;border-bottom:2.5px solid var(--green)}
h2{font-size:1.2rem;color:var(--green);margin:32px 0 12px;padding-left:12px;border-left:5px solid var(--sakura);line-height:1.5}
h3{font-size:1.04rem;color:var(--green);margin:22px 0 8px}
h4{font-size:.98rem;margin:18px 0 6px}
p{margin:0 0 13px}
ul,ol{margin:0 0 14px 22px}li{margin-bottom:5px}
hr{border:0;border-top:1px solid var(--line);margin:26px 0}
a{color:#2E6B58}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.87em;background:#F2F4F5;padding:1px 5px;border-radius:4px;word-break:break-all}
pre{background:#1E2A26;color:#E8EFEB;padding:16px 18px;border-radius:10px;overflow-x:auto;margin:0 0 16px;font-size:.84rem;line-height:1.7}
pre code{background:none;padding:0;color:inherit;word-break:normal}
blockquote{border-left:4px solid var(--sakura);background:#FCEFF2;padding:11px 18px;border-radius:0 8px 8px 0;margin:0 0 16px}
blockquote p{margin:0}
.tw{overflow-x:auto;margin:0 0 18px}
table{border-collapse:collapse;width:100%;font-size:.9rem;min-width:520px}
th{background:var(--green);color:#fff;text-align:left;padding:9px 11px;font-size:.84rem;white-space:nowrap}
td{padding:8px 11px;border-top:1px solid #EDF0F1;vertical-align:top}
tbody tr:nth-child(even){background:#FAFBFB}
@media(max-width:700px){.sheet{padding:22px 18px 46px}body{font-size:15.5px}h1{font-size:1.34rem}}
"""

for src, dst, title in DOCS:
    body = md2html((SRC / src).read_text(encoding="utf-8"))
    (OUT / dst).write_text(f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{NOINDEX}
<title>{html.escape(title)}</title>
<style>{CSS}</style></head>
<body><div class="sheet"><a class="back" href="./">&larr; 資料一覧にもどる</a>
{body}
</div></body></html>""", encoding="utf-8")

# ---------- 3. 既存HTMLに noindex を注入 ----------
for p in list(OUT.glob("*.html")) + list((OUT / "mockup").glob("*.html")):
    s = p.read_text(encoding="utf-8")
    if 'name="robots"' not in s:
        p.write_text(s.replace("<head>", "<head>\n" + NOINDEX, 1), encoding="utf-8")

(OUT / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
(OUT / ".nojekyll").write_text("", encoding="utf-8")

print("files:", sum(1 for p in OUT.rglob('*') if p.is_file()))
