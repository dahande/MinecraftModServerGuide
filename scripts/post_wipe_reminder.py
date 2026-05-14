#!/usr/bin/env python3
"""
7DTD サーバーワイプの段階的リマインダーを Discord に投稿する。

実行時の現在時刻 (UTC) に対応するリマインダーを選び、@everyone 付きで送信。
GitHub Actions の schedule から呼ばれ、リマインダー時刻ごとに 1 回ずつ発火する想定。

環境変数:
  DISCORD_WEBHOOK_URL  (必須)  投稿先 (7DTDチャンネル) Webhook URL
  SITE_URL             任意    記事リンクの基点
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone


SITE_URL = os.environ.get(
    "SITE_URL", "https://dahande.github.io/MinecraftModServerGuide"
).rstrip("/")
WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

WIPE_AT_JST = "2026年6月12日（金）24:00"
ARTICLE_URL = f"{SITE_URL}/news.html#news-20260430-wipe"

JST = timezone(timedelta(hours=9))

# 各リマインダーは (発火日時 JST, タイトル, 本文) のタプル。
# 発火日時 ±90分 のウィンドウ内で実行された場合に該当する。
REMINDERS = [
    (
        datetime(2026, 5, 13, 21, 0, tzinfo=JST),
        "🛑 サーバー一時休止まで あと1ヶ月",
        f"【JP/PvP/日本公式鯖】血祭だぁ！ は **{WIPE_AT_JST}** をもってワイプ (一時休止) となります。\n"
        "**サーバー内データは全て削除** されますので、ベースのスクリーンショットなど思い出を残しておいてください。",
    ),
    (
        datetime(2026, 5, 29, 21, 0, tzinfo=JST),
        "⏰ サーバーワイプまで あと2週間",
        f"**{WIPE_AT_JST}** にサーバー停止 (データ全削除) を予定しています。\n"
        "再開予定はありますが時期は未定です。残り期間を楽しみましょう。",
    ),
    (
        datetime(2026, 6, 5, 21, 0, tzinfo=JST),
        "📅 サーバーワイプまで あと1週間",
        f"**{WIPE_AT_JST}** にサーバー停止 (データ全削除) です。\n"
        "やり残しのないように！ ラストブラッドムーン等、悔いのないプレイを。",
    ),
    (
        datetime(2026, 6, 11, 21, 0, tzinfo=JST),
        "🔔 明日 24:00 にワイプ実施",
        "**残り24時間** でサーバー停止 (全データ削除) です。\n"
        "最後のスクショ撮影・思い出シェアはお早めに！",
    ),
    (
        datetime(2026, 6, 12, 18, 0, tzinfo=JST),
        "🚨 本日 24:00 ワイプ (約6時間後)",
        "**本日 24:00** をもって 7DTD サーバーは一時休止となります。\n"
        "全てのデータが削除されますので、残しておきたいものは今のうちに記録を！",
    ),
    (
        datetime(2026, 6, 12, 23, 0, tzinfo=JST),
        "⚠️ 1時間後にサーバーワイプ",
        "**残り 1 時間** でサーバー停止します。\n"
        "ご利用ありがとうございました。再開時にまたお会いしましょう 👋",
    ),
]

WINDOW_MIN = 90  # 発火時刻 ±90分の遅延までは対応 (GitHub Actions cron 遅延対策)


def pick_reminder():
    now = datetime.now(tz=JST)
    closest = None
    min_diff = None
    for at, title, body in REMINDERS:
        diff = abs((now - at).total_seconds()) / 60.0
        if diff <= WINDOW_MIN:
            if min_diff is None or diff < min_diff:
                closest = (at, title, body)
                min_diff = diff
    return closest


def build_embed(title, body):
    return {
        "title": title,
        "description": body,
        "url":   ARTICLE_URL,
        "color": 0xF87171,  # 7DTD カラー (赤)
        "footer": {"text": "のんびりサバイバル鯖 / ワイプリマインダー"},
    }


def post_to_discord(embed):
    payload = {
        "username":         "のんびりサバイバル鯖",
        "content":          "@everyone",
        "embeds":           [embed],
        "allowed_mentions": {"parse": ["everyone"]},
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK,
        data=data,
        headers={
            "Content-Type": "application/json; charset=utf-8",
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

    picked = pick_reminder()
    if picked is None:
        now = datetime.now(tz=JST).strftime("%Y-%m-%d %H:%M JST")
        print(f"no reminder matches now ({now}); skipping.")
        return 0

    at, title, body = picked
    post_to_discord(build_embed(title, body))
    print(f"posted: {at.isoformat()} / {title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
