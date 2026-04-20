"""
7 Days to Die status API.

Deployed on Fly.io. Queries the game server via Steam A2S protocol
(UDP) and returns JSON to the static site. Short in-memory cache
prevents hammering the game server when multiple browsers poll.
"""
import os
import socket
import threading
import time
from datetime import datetime, timezone

import a2s
from flask import Flask, jsonify, make_response, request


SERVER_HOST   = os.environ.get("SERVER_HOST", "220.158.24.94")
SERVER_PORT   = int(os.environ.get("SERVER_PORT", "26900"))
CACHE_SEC     = int(os.environ.get("CACHE_SEC", "20"))
QUERY_TIMEOUT = float(os.environ.get("QUERY_TIMEOUT", "3"))
ALLOW_ORIGINS = [
    o.strip()
    for o in os.environ.get("ALLOW_ORIGINS", "https://dahande.github.io").split(",")
    if o.strip()
]

app = Flask(__name__)

_cache = {"payload": None, "at": 0.0}
_lock  = threading.Lock()


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _query():
    addr = (SERVER_HOST, SERVER_PORT)
    try:
        info = a2s.info(addr, timeout=QUERY_TIMEOUT)
    except (socket.timeout, ConnectionError, OSError) as e:
        return {
            "ok":         False,
            "status":     "offline",
            "host":       SERVER_HOST,
            "port":       SERVER_PORT,
            "players":    0,
            "maxPlayers": 64,
            "playerList": [],
            "error":      str(e),
            "checkedAt":  _now_iso(),
        }

    try:
        players = a2s.players(addr, timeout=QUERY_TIMEOUT)
    except (socket.timeout, ConnectionError, OSError):
        players = []

    return {
        "ok":         True,
        "status":     "online",
        "host":       SERVER_HOST,
        "port":       SERVER_PORT,
        "name":       info.server_name or "",
        "map":        info.map_name    or "",
        "game":       info.game        or "",
        "version":    info.version     or "",
        "players":    int(info.player_count or 0),
        "maxPlayers": int(info.max_players  or 64),
        "bots":       int(info.bot_count    or 0),
        "ping":       round(float(info.ping or 0) * 1000, 1),
        "password":   bool(info.password_protected),
        "vac":        bool(info.vac_enabled),
        "playerList": [
            {
                "name":     p.name or "",
                "score":    int(p.score or 0),
                "duration": round(float(p.duration or 0), 1),
            }
            for p in players
            if (p.name or "").strip()
        ],
        "checkedAt":  _now_iso(),
    }


def _cached():
    now = time.time()
    with _lock:
        if _cache["payload"] and now - _cache["at"] < CACHE_SEC:
            return _cache["payload"]
        payload = _query()
        _cache["payload"] = payload
        _cache["at"]      = now
        return payload


def _apply_cors(resp, origin):
    if origin and origin in ALLOW_ORIGINS:
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Vary"] = "Origin"


@app.get("/status")
def status():
    payload = _cached()
    resp = make_response(jsonify(payload))
    _apply_cors(resp, request.headers.get("Origin", ""))
    resp.headers["Cache-Control"] = f"public, max-age={CACHE_SEC}"
    return resp


@app.route("/status", methods=["OPTIONS"])
def status_preflight():
    resp = make_response("", 204)
    _apply_cors(resp, request.headers.get("Origin", ""))
    resp.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    resp.headers["Access-Control-Max-Age"]      = "86400"
    return resp


@app.get("/")
def root():
    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
