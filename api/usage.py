"""Anonymous usage log: one JSON line per /compare call, no farmer identity, no coordinates.

USAGE_LOG sets the file (default data/usage.jsonl). /admin/stats needs ADMIN_TOKEN; unset = disabled.
"""
import json
import os
import secrets
import statistics
import time
from collections import Counter

from fastapi import APIRouter, Header, HTTPException

router = APIRouter()


def _path() -> str:
    return os.environ.get("USAGE_LOG", "data/usage.jsonl")


def record(req: dict, served: bool, started: float) -> None:
    row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "location": req.get("location") or "gps",
           "rotation": req.get("current_rotation"), "water_source": req.get("water_source"),
           "priorities": req.get("priorities", []), "served": served,
           "latency_ms": round((time.perf_counter() - started) * 1000)}
    try:
        with open(_path(), "a") as f:
            f.write(json.dumps(row) + "\n")
    except OSError:
        pass  # logging must never break a farmer's request


@router.get("/admin/stats")
def stats(x_admin_token: str = Header(default="")):
    token = os.environ.get("ADMIN_TOKEN")
    if not token:
        raise HTTPException(status_code=404)
    if not secrets.compare_digest(x_admin_token, token):
        raise HTTPException(status_code=401)
    try:
        rows = [json.loads(line) for line in open(_path())]
    except FileNotFoundError:
        rows = []
    lat = [r["latency_ms"] for r in rows]
    return {"requests": len(rows),
            "served": sum(r["served"] for r in rows),
            "by_location": dict(Counter(r["location"] for r in rows)),
            "by_priority": dict(Counter(p for r in rows for p in r["priorities"])),
            "by_rotation": dict(Counter(r["rotation"] for r in rows)),
            "p50_latency_ms": statistics.median(lat) if lat else 0,
            "max_latency_ms": max(lat, default=0)}
