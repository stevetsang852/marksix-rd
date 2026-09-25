"""Fetch official / fallback Mark Six draws and persist raw JSON."""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import requests

from .schema import Draw

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"

HKJC_CANDIDATES = [
    "https://bet.hkjc.com/contentserver/jcbw/cmc/last30draw.json",
    "https://bet.hkjc.com/contentserver/jcbw/cmc/last30draw.js",
]

USER_AGENT = (
    "marksix-rd/0.1 research-bot (+https://github.com/stevetsang852/marksix-rd)"
)


def fetch_raw(url: str, timeout: int = 30) -> tuple[int, str, bytes]:
    r = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json,text/plain,*/*"},
        allow_redirects=True,
    )
    return r.status_code, r.headers.get("content-type", ""), r.content


def save_raw_snapshot(payload: bytes, label: str = "hkjc") -> Path:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = DATA_RAW / f"{label}_{day}.bin"
    path.write_bytes(payload)
    text_path = DATA_RAW / f"{label}_{day}.txt"
    try:
        text_path.write_text(payload.decode("utf-8", errors="replace"), encoding="utf-8")
    except OSError:
        pass
    return path


def _as_int(v: Any) -> int | None:
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    m = re.search(r"\d+", s)
    return int(m.group()) if m else None


def parse_hkjc_last30(obj: Any) -> list[Draw]:
    if isinstance(obj, list):
        rows = obj
    elif isinstance(obj, dict):
        for key in ("last30Draw", "lastDraw", "data", "draws", "results"):
            if isinstance(obj.get(key), list):
                rows = obj[key]
                break
        else:
            rows = [obj]
    else:
        return []

    out: list[Draw] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        nums = []
        for i in range(1, 7):
            val = None
            for k in (f"n{i}", f"no{i}", f"num{i}", f"number{i}", f"N{i}"):
                if k in item:
                    val = _as_int(item[k])
                    break
            if val is None and "nos" in item and isinstance(item["nos"], list) and len(item["nos"]) >= i:
                val = _as_int(item["nos"][i - 1])
            nums.append(val)
        special = None
        for k in ("specialNumber", "special", "sno", "extra", "sNo", "spNo"):
            if k in item:
                special = _as_int(item[k])
                break
        issue = str(item.get("id") or item.get("issue") or item.get("issueNo") or item.get("drawNo") or item.get("period") or "")
        date = str(item.get("date") or item.get("drawDate") or item.get("openDate") or "")
        if all(nums) and special:
            out.append(Draw(issue=issue, date=date[:10], n1=nums[0], n2=nums[1], n3=nums[2], n4=nums[3], n5=nums[4], n6=nums[5], special=special, source="hkjc"))
    return out


def parse_any_json_bytes(payload: bytes) -> list[Draw]:
    text = payload.decode("utf-8", errors="replace").strip()
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")
    if text.startswith("callback(") or text.startswith("jQuery"):
        text = text[text.find("(") + 1 : text.rfind(")")]
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return []
    return parse_hkjc_last30(obj)


def load_csv(path: Path, source: str = "csv") -> list[Draw]:
    draws: list[Draw] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            nums = []
            for i in range(1, 7):
                val = None
                for k in (f"n{i}", f"N{i}", f"no{i}", f"num{i}"):
                    if k in row and row[k]:
                        val = int(row[k])
                        break
                nums.append(val)
            special = None
            for k in ("special", "specialNumber", "extra", "sno"):
                if k in row and row[k]:
                    special = int(row[k])
                    break
            if all(nums) and special:
                draws.append(Draw(
                    issue=str(row.get("issue") or row.get("id") or row.get("draw") or ""),
                    date=str(row.get("date") or row.get("drawDate") or "")[:10],
                    n1=nums[0], n2=nums[1], n3=nums[2], n4=nums[3], n5=nums[4], n6=nums[5],
                    special=special, source=source,
                ))
    return draws


def _dedupe(draws: list[Draw]) -> list[Draw]:
    seen: set[str] = set()
    out: list[Draw] = []
    for d in draws:
        key = d.issue or f"{d.date}-{d.mains}-{d.special}"
        if key in seen:
            continue
        seen.add(key)
        out.append(d)
    out.sort(key=lambda d: (d.date, d.issue))
    return out


def write_processed(draws: list[Draw]) -> Path:
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    path = DATA_PROCESSED / "draws.json"
    path.write_text(json.dumps([d.to_dict() for d in _dedupe(draws)], ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_processed() -> list[Draw]:
    path = DATA_PROCESSED / "draws.json"
    if not path.exists():
        sample = ROOT / "data" / "sample_draws.csv"
        if sample.exists():
            return load_csv(sample, source="sample")
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Draw(issue=r["issue"], date=r["date"], n1=int(r["n1"]), n2=int(r["n2"]), n3=int(r["n3"]), n4=int(r["n4"]), n5=int(r["n5"]), n6=int(r["n6"]), special=int(r["special"]), source=r.get("source", "processed")) for r in raw]


def ingest_cli() -> dict[str, Any]:
    meta: dict[str, Any] = {"tried": [], "parsed": 0, "ok": False}
    all_draws: list[Draw] = []
    for url in HKJC_CANDIDATES:
        try:
            status, ctype, body = fetch_raw(url)
            snap = save_raw_snapshot(body, label="hkjc")
            meta["tried"].append({"url": url, "status": status, "content_type": ctype, "bytes": len(body), "snap": str(snap)})
            parsed = parse_any_json_bytes(body)
            if parsed:
                all_draws.extend(parsed)
                meta["ok"] = True
        except requests.RequestException as exc:
            meta["tried"].append({"url": url, "error": str(exc)})
    existing = load_processed()
    merged = _dedupe(existing + all_draws)
    write_processed(merged)
    meta["parsed"] = len(all_draws)
    meta["total"] = len(merged)
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    (DATA_RAW / "last_ingest_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


if __name__ == "__main__":
    print(json.dumps(ingest_cli(), ensure_ascii=False, indent=2))
