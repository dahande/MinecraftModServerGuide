#!/usr/bin/env python3
"""
news.html から新規お知らせ記事を抽出して Discord Webhook に投稿する。

対象記事の判定は .github/news-posted.json に既投稿 ID を記録して差分を取る。
初回実行時は既存記事を全てロック (投稿せずIDだけ記録) し、以降に追加された
記事だけ投稿する。

環境変数:
  DISCORD_WEBHOOK_URL  (必須)  投稿先 Webhook URL
  SITE_URL             任意    記事リンクの基点 (デフォルト: GitHub Pages URL)
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

REPO      = Path(__file__).resolve().parent.parent
NEWS_HTML = REPO / "news.html"
STATE     = REPO / ".github" / "news-posted.json"

SITE_URL = os.environ.get(
    "SITE_URL",
    "https://dahande.github.io/MinecraftModServerGuide",
).rstrip("/")
WEBHOOK  = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

# タグ別のサイドバー色 (Discord embed の左側バー)
TAG_COLORS = {
    "イベント": 0xFBBF24,   # オレンジ
    "更新":     0x4ADE80,   # グリーン
    "お知らせ": 0x4D9FFF,   # ブルー
}
DEFAULT_COLOR = 0x4D9FFF


def load_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"posted": []}


def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _text(node):
    """連続空白を整理して取り出す。"""
    if node is None:
        return ""
    return " ".join(node.get_text(" ", strip=True).split())


def extract_articles():
    soup = BeautifulSoup(NEWS_HTML.read_text(encoding="utf-8"), "html.parser")
    out = []
    for art in soup.find_all("article", class_="news-article"):
        aid = art.get("id", "").strip()
        if not aid:
            continue
        body = art.select_one(".news-article__body")
        paragraphs = []
        if body:
            for p in body.find_all("p"):
                t = _text(p)
                if t:
                    paragraphs.append(t)
        out.append({
            "id":    aid,
            "tag":   _text(art.select_one(".news-item__tag")),
            "date":  _text(art.select_one(".news-article__date")),
            "title": _text(art.select_one(".news-article__title")),
            "body":  "\n\n".join(paragraphs),
        })
    return out


def build_embed(article):
    body = article["body"]
    if len(body) > 900:
        body = body[:897] + "…"

    footer_bits = [b for b in (article["tag"], article["date"]) if b]

    return {
        "title":       article["title"][:256],
        "url":         f"{SITE_URL}/news.html#{article['id']}",
        "description": body,
        "color":       TAG_COLORS.get(article["tag"], DEFAULT_COLOR),
        "footer":      {"text": " • ".join(footer_bits)} if footer_bits else None,
    }


def post_to_discord(embed):
    payload = {
        "username": "のんびりサバイバル鯖",
        "embeds":   [{k: v for k, v in embed.items() if v is not None}],
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req  = urllib.request.Request(
        WEBHOOK,
        data=data,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            # Cloudflare が Python-urllib デフォルトUAを 403 で弾くので明示
            "User-Agent":   "NonbiriServerBot (https://github.com/dahande/minecraftmodserverguide, 1.0)",
        },
        method="POST",
    )

    last_err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp.read()
                return
        except urllib.error.HTTPError as e:
            # 429 Rate Limit - Retry-After を尊重
            if e.code == 429:
                retry = 2 ** attempt
                try:
                    retry = float(e.headers.get("Retry-After", retry))
                except (TypeError, ValueError):
                    pass
                time.sleep(min(retry, 30))
                last_err = e
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"discord webhook failed: {last_err}")


def main():
    if not WEBHOOK:
        print("DISCORD_WEBHOOK_URL is not set; skipping.")
        return 0

    if not NEWS_HTML.exists():
        print(f"{NEWS_HTML} not found; nothing to do.")
        return 0

    first_run = not STATE.exists()
    state     = load_state()
    posted    = set(state.get("posted", []))

    articles = extract_articles()

    if first_run:
        state["posted"] = sorted({a["id"] for a in articles})
        save_state(state)
        print(f"bootstrap: recorded {len(articles)} existing articles without posting.")
        return 0

    # news.html は新しい記事が上に追加されるので、Discord には古い→新しい順で
    # 投稿して新しい記事が下(最新)に来るようにする
    new_articles = [a for a in articles if a["id"] not in posted]
    if not new_articles:
        print("no new articles.")
        return 0

    for article in reversed(new_articles):
        post_to_discord(build_embed(article))
        posted.add(article["id"])
        print(f"posted: {article['id']} / {article['title']}")

    state["posted"] = sorted(posted)
    save_state(state)
    print(f"done: {len(new_articles)} article(s) posted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
