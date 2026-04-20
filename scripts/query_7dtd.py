#!/usr/bin/env python3
"""
7 Days to Die server monitor.

Queries the target server via Steam A2S (Source Engine Query) protocol and
writes the result to data/7dtd-status.json for the static site to consume.

This replaces the previous battlemetrics.com dependency – the status pipeline
is now fully self-hosted in this repository via GitHub Actions.
"""
import json
import os
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import a2s

SERVER_HOST = os.environ.get("SERVER_HOST", "220.158.24.94")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "26900"))
TIMEOUT_SEC = float(os.environ.get("QUERY_TIMEOUT", "5"))
MAX_HISTORY = 2016  # 7 days at 5-minute cadence

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_FILE = REPO_ROOT / "data" / "7dtd-status.json"


def query_once(addr):
    info = a2s.info(addr, timeout=TIMEOUT_SEC)
    try:
        players = a2s.players(addr, timeout=TIMEOUT_SEC)
    except (socket.timeout, ConnectionError, OSError):
        players = []
    return info, players


def build_payload():
    addr = (SERVER_HOST, SERVER_PORT)
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    last_err = None
    for attempt in range(3):
        try:
            info, players = query_once(addr)
            return {
                "ok": True,
                "status": "online",
                "host": SERVER_HOST,
                "port": SERVER_PORT,
                "name": getattr(info, "server_name", "") or "",
                "map": getattr(info, "map_name", "") or "",
                "game": getattr(info, "game", "") or "",
                "version": getattr(info, "version", "") or "",
                "players": int(getattr(info, "player_count", 0) or 0),
                "maxPlayers": int(getattr(info, "max_players", 64) or 64),
                "bots": int(getattr(info, "bot_count", 0) or 0),
                "ping": round(float(getattr(info, "ping", 0.0) or 0.0) * 1000, 1),
                "password": bool(getattr(info, "password_protected", False)),
                "vac": bool(getattr(info, "vac_enabled", False)),
                "playerList": [
                    {
                        "name": p.name or "",
                        "score": int(p.score or 0),
                        "duration": round(float(p.duration or 0.0), 1),
                    }
                    for p in players
                    if (p.name or "").strip()
                ],
                "checkedAt": now_iso,
            }
        except (socket.timeout, ConnectionError, OSError) as e:
            last_err = str(e)
            time.sleep(1 + attempt)

    return {
        "ok": False,
        "status": "offline",
        "host": SERVER_HOST,
        "port": SERVER_PORT,
        "players": 0,
        "maxPlayers": 64,
        "playerList": [],
        "error": last_err or "unreachable",
        "checkedAt": now_iso,
    }


def load_existing():
    if OUT_FILE.exists():
        try:
            return json.loads(OUT_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def main():
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    prev = load_existing()

    payload = build_payload()

    history = prev.get("history") or []
    history.append({
        "t": payload["checkedAt"],
        "p": payload["players"],
        "on": payload["status"] == "online",
    })
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]
    payload["history"] = history

    stats = prev.get("stats") or {"peak": 0, "onChecks": 0, "total": 0}
    stats["total"] = int(stats.get("total", 0)) + 1
    if payload["status"] == "online":
        stats["onChecks"] = int(stats.get("onChecks", 0)) + 1
        if payload["players"] > int(stats.get("peak", 0)):
            stats["peak"] = payload["players"]
    payload["stats"] = stats

    OUT_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"status={payload['status']} players={payload['players']}/{payload['maxPlayers']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
