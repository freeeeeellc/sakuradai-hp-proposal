"""crawl.json + lastmod.json から、全ページ一覧の単一HTMLを生成する。
使い方: cd _audit && python3 gen_list.py
出力:   ../04_ページ一覧.html
"""
import json, collections, html, pathlib

SEC = {
    '(root)': 'トップ（フレーム）',
    'kairan': '回覧板', 'jichikai_files': '自治会ファイル', 'Gijiroku': '議事録',
    'jichi_kaikan_annnai': '自治会館の案内', 'senmonbu': '専門部活動', 'event': '桜台のイベント',
    'kouhoushi': '広報誌', 'chiiki_katudou': '地域活動・ボランティア', 'circle_group': 'サークル・グループ',
    'minnanohiroba': 'みんなの広場', 'seikatu_jouho': '生活情報', 'calendar': '自治会カレンダー',
    'topix': 'トピックス', 'chiku_joho': '地区情報', '_100_title': 'その他',
}
ORDER = list(SEC)
STOP = '2024-07-28'          # 旧ドメインからの移行日。ここで一斉に止まっている
BASE = 'https://xn--6oqs1jd2v68dy45a.com/'

d = json.load(open('crawl.json'))
P, ASSETS = d['pages'], d['assets']
LM = json.load(open('lastmod.json'))


def sec_of(path):
    return path.split('/')[0] if '/' in path else '(root)'


def status_of(date):
    if date > '2026-01-01':
        return ('live', '稼働中')
    if date > '2025-01-01':
        return ('slow', '低頻度')
    return ('stop', '停止')


rows = []
for path, rec in P.items():
    date = LM.get(path) or '-'
    cls, label = status_of(date)
    rows.append({
        'sec': sec_of(path), 'path': path,
        'title': rec.get('title') or '(無題)',
        'date': date, 'cls': cls, 'label': label,
    })
rows.sort(key=lambda r: (ORDER.index(r['sec']) if r['sec'] in ORDER else 99, r['date'] != STOP, r['path']))

pdf = collections.Counter(sec_of(a) for a in ASSETS)
pages = collections.Counter(r['sec'] for r in rows)
live = collections.Counter(r['sec'] for r in rows if r['cls'] != 'stop')
newest = {}
for r in rows:
    if r['date'] > newest.get(r['sec'], ''):
        newest[r['sec']] = r['date']

n_live = sum(1 for r in rows if r['cls'] == 'live')
n_slow = sum(1 for r in rows if r['cls'] == 'slow')
n_stop = sum(1 for r in rows if r['cls'] == 'stop')

e = html.escape

sec_rows = []
for s in ORDER:
    if s not in pages:
        continue
    ratio = live.get(s, 0)
    sec_rows.append(f"""<tr>
      <td><b>{e(SEC[s])}</b><br><span class="dim">{'/' if s=='(root)' else '/'+e(s)}</span></td>
      <td class="num">{pages[s]}</td>
      <td class="num">{pdf.get(s,0) or '—'}</td>
      <td class="num">{'<b class="ok">'+str(ratio)+'</b>' if ratio else '<span class="dim">0</span>'}</td>
      <td class="num">{e(newest.get(s,'-'))}</td>
      <td>{'<span class="b live">更新中</span>' if newest.get(s,'') > '2025-01-01' else '<span class="b stop">停止</span>'}</td>
    </tr>""")

page_rows = []
for r in rows:
    page_rows.append(f"""<tr data-s="{r['cls']}" data-k="{e(r['path']+' '+r['title']+' '+SEC.get(r['sec'],r['sec']))}">
      <td class="sec">{e(SEC.get(r['sec'], r['sec']))}</td>
      <td class="path"><a href="{BASE}{e(r['path'])}" target="_blank" rel="noopener">/{e(r['path'])}</a></td>
      <td>{e(r['title'])}</td>
      <td class="num">{e(r['date'])}</td>
      <td><span class="b {r['cls']}">{r['label']}</span></td>
    </tr>""")

out = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>桜台自治会.com　全ページ一覧と更新状況</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;padding:28px 20px 60px;background:#F4F6F5;color:#1B2025;
 font-family:"Hiragino Kaku Gothic ProN","Hiragino Sans","Yu Gothic Medium","Yu Gothic",Meiryo,sans-serif;
 font-size:14px;line-height:1.7}}
.wrap{{max-width:1180px;margin:0 auto}}
h1{{font-size:1.5rem;color:#1F4B3F;margin:0 0 6px;letter-spacing:.04em}}
.sub{{color:#5A646D;font-size:.86rem;margin:0 0 22px}}
h2{{font-size:1.1rem;color:#1F4B3F;margin:34px 0 12px;padding-left:11px;border-left:5px solid #C4506E}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:8px}}
.card{{background:#fff;border:1px solid #E2E6E8;border-radius:12px;padding:16px 18px}}
.card b{{display:block;font-size:1.9rem;line-height:1.25;color:#1F4B3F}}
.card span{{font-size:.8rem;color:#5A646D}}
.card.stop b{{color:#B9483F}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;
 box-shadow:0 1px 2px rgba(20,40,30,.05),0 4px 14px rgba(20,40,30,.05)}}
th{{background:#1F4B3F;color:#fff;font-size:.82rem;text-align:left;padding:11px 13px;white-space:nowrap}}
td{{padding:10px 13px;border-top:1px solid #EDF0F1;vertical-align:top;font-size:.87rem}}
tbody tr:hover{{background:#F7F9F8}}
.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
td.sec{{white-space:nowrap;color:#5A646D;font-size:.82rem}}
td.path{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.78rem;word-break:break-all;max-width:340px}}
td.path a{{color:#2E6B58;text-decoration:none}}
td.path a:hover{{text-decoration:underline}}
.dim{{color:#98A1A8;font-size:.78rem}}
.ok{{color:#1F4B3F}}
.b{{display:inline-block;font-size:.74rem;font-weight:700;padding:3px 10px;border-radius:999px;white-space:nowrap}}
.b.live{{background:#E4F1EA;color:#1F5C40}}
.b.slow{{background:#FFF3DC;color:#8A6114}}
.b.stop{{background:#F2F4F5;color:#79838B}}
.tools{{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:0 0 12px}}
.tools button{{font:inherit;font-size:.84rem;min-height:40px;padding:0 15px;border:1.5px solid #D8DEE1;
 background:#fff;border-radius:9px;cursor:pointer;color:#1B2025}}
.tools button[aria-pressed=true]{{background:#1F4B3F;border-color:#1F4B3F;color:#fff;font-weight:700}}
.tools input{{font:inherit;font-size:.86rem;min-height:40px;padding:0 13px;flex:1;min-width:190px;
 border:1.5px solid #D8DEE1;border-radius:9px}}
.count{{color:#5A646D;font-size:.82rem;white-space:nowrap}}
.note{{background:#FFF7F8;border:1px solid #F0CBD5;border-radius:10px;padding:13px 16px;font-size:.85rem;margin:14px 0 0}}
@media(max-width:820px){{
  .cards{{grid-template-columns:repeat(2,1fr)}}
  td.sec,th.sec{{display:none}}
  td.path{{max-width:none}}
}}
</style>
</head>
<body>
<div class="wrap">

<h1>桜台自治会.com　全ページ一覧と更新状況</h1>
<p class="sub">2026年8月4日にサイト全体を実際にたどって取得（HTMLページ252件／PDF・文書2,743件）。
更新日はサーバーが返す Last-Modified の実測値です。</p>

<div class="cards">
  <div class="card"><b>252</b><span>HTMLページ総数</span></div>
  <div class="card"><b>{n_live}</b><span>稼働中（2026年に更新）</span></div>
  <div class="card"><b>{n_slow}</b><span>低頻度（2025年に更新）</span></div>
  <div class="card stop"><b>{n_stop}</b><span>停止（2024-07-28で一斉）</span></div>
</div>

<div class="note"><b>230ページが2024年7月28日という同一日で止まっています。</b>
これは旧ドメイン <code>www.i-sakuradai.jp</code> から現ドメインへ移行した際の一括アップロード日と考えられます。
つまりその日以降、実際に手が入っているのは <b>22ページだけ</b>です。</div>

<h2>区分別のまとめ</h2>
<table>
<thead><tr><th>区分</th><th class="num">ページ数</th><th class="num">PDF等</th><th class="num">更新継続</th><th class="num">最終更新</th><th>状態</th></tr></thead>
<tbody>
{''.join(sec_rows)}
</tbody>
</table>

<h2>全252ページの一覧</h2>
<div class="tools">
  <button data-f="all" aria-pressed="true">すべて（252）</button>
  <button data-f="live" aria-pressed="false">稼働中（{n_live}）</button>
  <button data-f="slow" aria-pressed="false">低頻度（{n_slow}）</button>
  <button data-f="stop" aria-pressed="false">停止（{n_stop}）</button>
  <input id="q" type="search" placeholder="ページ名・URLで絞り込み（例：回覧、gomi）">
  <span class="count" id="cnt"></span>
</div>
<table>
<thead><tr><th class="sec">区分</th><th>URL</th><th>ページ名</th><th class="num">最終更新</th><th>状態</th></tr></thead>
<tbody id="tb">
{''.join(page_rows)}
</tbody>
</table>

</div>
<script>
var rows = [].slice.call(document.querySelectorAll('#tb tr'));
var filter = 'all', q = '';
function apply() {{
  var n = 0;
  rows.forEach(function (r) {{
    var ok = (filter === 'all' || r.dataset.s === filter) &&
             (!q || r.dataset.k.toLowerCase().indexOf(q) > -1);
    r.style.display = ok ? '' : 'none';
    if (ok) n++;
  }});
  document.getElementById('cnt').textContent = n + '件を表示';
}}
document.querySelectorAll('.tools button').forEach(function (b) {{
  b.addEventListener('click', function () {{
    document.querySelectorAll('.tools button').forEach(function (x) {{ x.setAttribute('aria-pressed', 'false'); }});
    b.setAttribute('aria-pressed', 'true');
    filter = b.dataset.f; apply();
  }});
}});
document.getElementById('q').addEventListener('input', function (ev) {{
  q = ev.target.value.trim().toLowerCase(); apply();
}});
apply();
</script>
</body>
</html>
"""

p = pathlib.Path('../04_ページ一覧.html')
p.write_text(out, encoding='utf-8')
print('wrote', p.resolve(), p.stat().st_size, 'bytes')
print(f'live={n_live} slow={n_slow} stop={n_stop} total={len(rows)}')
