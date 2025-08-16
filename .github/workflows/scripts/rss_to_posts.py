#!/usr/bin/env python3
# scripts/rss_to_posts.py
# 1日1本、RSSの最新記事を要約して /posts/ にHTML生成（依存ライブラリなし）

import os, re, html, hashlib
from datetime import datetime, timezone, timedelta
import urllib.request
import xml.etree.ElementTree as ET

# ====== 設定（必要ならここだけ編集） ======
JST = timezone(timedelta(hours=9))
SITE_TITLE = "自動化アフィリエイトブログ"
POSTS_DIR = "posts"
MAX_ITEMS = 1  # 1日あたり作る記事数（まずは1本）
RSS_FEEDS = [
    "https://rss.itmedia.co.jp/rss/2.0/news_bursts.xml",  # 例: IT系速報
    # "https://example.com/feed",
]
TEMPLATE = """<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="../style.css"></head>
<body>
<header><h1>{site}</h1><nav><ul>
  <li><a href="../index.html">ホーム</a></li>
</ul></nav></header>
<main class="container">
  <article class="card">
    <h2>{title}</h2>
    <p class="meta">{date}</p>
    <p>{summary}</p>
    <p><a href="{link}" target="_blank" rel="noopener">元記事を見る</a></p>
    <hr>
    <div class="ad-slot"><!-- 広告/アフィリエイトタグをここに貼る --></div>
  </article>
</main>
<footer><p>© {year} {site}</p></footer>
</body></html>"""
# ==========================================

def _fetch(url:str)->bytes:
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (RSS bot)"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read()

def _strip(txt:str)->str:
    txt = re.sub(r"<[^>]+>", "", txt or "")
    txt = html.unescape(txt).strip()
    return re.sub(r"\s+", " ", txt)

def _summary(txt:str, n=160)->str:
    s = _strip(txt)
    return (s[:n] + "…") if len(s) > n else s

def main():
    os.makedirs(POSTS_DIR, exist_ok=True)
    created = 0
    for feed in RSS_FEEDS:
        try:
            raw = _fetch(feed)
            root = ET.fromstring(raw)
            items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
            for it in items[:MAX_ITEMS]:
                title = (it.findtext("title") or it.findtext("{http://www.w3.org/2005/Atom}title") or "No title").strip()
                # RSSの<link>か、Atomの<link href="...">
                link = (it.findtext("link") or "")
                if not link:
                    lk = it.find("{http://www.w3.org/2005/Atom}link")
                    link = lk.get("href") if lk is not None else ""
                desc = (it.findtext("description") or it.findtext("{http://www.w3.org/2005/Atom}summary") or "")
                uid = hashlib.md5((link or title).encode()).hexdigest()[:10]
                out = os.path.join(POSTS_DIR, f"{uid}.html")
                if os.path.exists(out):
                    continue  # 同一記事はスキップ
                now = datetime.now(JST)
                html_text = TEMPLATE.format(
                    site=SITE_TITLE,
                    title=html.escape(title),
                    date=now.strftime("%Y-%m-%d %H:%M"),
                    summary=html.escape(_summary(desc)),
                    link=html.escape(link),
                    year=now.year,
                )
                with open(out, "w", encoding="utf-8") as f:
                    f.write(html_text)
                created += 1
        except Exception as e:
            print("ERR feed:", feed, e)
    print(f"created {created} posts")

if __name__ == "__main__":
    main()
