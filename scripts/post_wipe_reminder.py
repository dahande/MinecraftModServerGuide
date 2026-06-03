#!/usr/bin/env python3
"""
7DTD サーバーワイプの段階的リマインダーを Discord に投稿する。

「送信済みリマインダーID」を状態ファイル (.github/wipe-reminders-sent.json) に
記録し、未送信かつ発火時刻を過ぎたものを送る。これにより GitHub Actions の
cron 遅延 (数十分〜数時間) があっても取りこぼさず、かつ二重送信もしない。

動作モード:
  通常 (schedule):  now >= 発火時刻 で未送信のリマインダーのうち「最新の1件」を送信。
                    それより前の未送信リマインダーは (送信済み扱いにして) 黙って繰り上げ。
                    → 遅延で1件飛ばしても、過去分を連投せず現在相当の1件だけ届く。
  FORCE_SEND=1:     状態に関わらず「現在時刻に最も近い」1件を即送信 (手動テスト/即時送信用)。
  どちらの場合も「送信した発火時刻以前」のIDを全て送信済みとして記録する。

環境変数:
  DISCORD_WEBHOOK_URL  (必須)  投稿先 (7DTDチャンネル) Webhook URL
  SITE_URL             任意    記事リンクの基点
  FORCE_SEND           任意    1/true で即時送信モード (workflow_dispatch 時に自動付与)
  WIPE_STATE_PATH      任意    状態ファイルのパス上書き (テスト用)
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


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

FORCE_SEND = os.environ.get("FORCE_SEND", "").strip().lower() in ("1", "true", "yes")

REPO       = Path(__file__).resolve().parent.parent
STATE_PATH = Path(
    os.environ.get("WIPE_STATE_PATH", str(REPO / ".github" / "wipe-reminders-sent.json"))
)


def reminder_id(at):
    """発火時刻から安定したIDを作る (例: 20260612T2300)。"""
    return at.strftime("%Y%m%dT%H%M")


def load_sent():
    if STATE_PATH.exists():
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            return set(data.get("sent", []))
        except (json.JSONDecodeError, OSError):
            pass
    return set()


def save_sent(sent):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps({"sent": sorted(sent)}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def pick_reminder(now, sent):
    """送信すべき (at, title, body) を返す。なければ None。

    - FORCE_SEND: now に最も近い1件 (状態を無視。手動の即時送信/テスト用)。
    - 通常:       発火時刻を過ぎていて (now >= at) 未送信のうち「最新の1件」。
                  cron が遅延して複数を跨いでも、最新だけ送り過去分は繰り上げる。
    """
    if FORCE_SEND:
        return min(REMINDERS, key=lambda r: abs((now - r[0]).total_seconds()))

    due_unsent = [
        r for r in REMINDERS
        if now >= r[0] and reminder_id(r[0]) not in sent
    ]
    if not due_unsent:
        return None
    return max(due_unsent, key=lambda r: r[0])


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

    now  = datetime.now(tz=JST)
    sent = load_sent()

    picked = pick_reminder(now, sent)
    if picked is None:
        print(f"no due/unsent reminder at {now:%Y-%m-%d %H:%M JST}; skipping.")
        return 0

    at, title, body = picked
    post_to_discord(build_embed(title, body))

    # 送信した発火時刻「以前」のリマインダーは全て送信済みとして記録する。
    # → 取りこぼした過去分を黙って繰り上げ、かつ後続 cron での二重送信を防ぐ。
    newly      = {reminder_id(r[0]) for r in REMINDERS if r[0] <= at}
    superseded = newly - sent - {reminder_id(at)}
    sent      |= newly
    save_sent(sent)

    print(f"posted: {reminder_id(at)} ({at:%Y-%m-%d %H:%M JST}) / {title}")
    if superseded:
        print(f"superseded (marked sent without posting): {sorted(superseded)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
