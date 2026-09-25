from __future__ import annotations
from datetime import date
from .schema import Draw

GENS = {
    "gen5": {"label": "第5代 · 現行主力", "blurb": "2026-05-05 起（26/047）", "start": date(2026, 5, 5), "end": None, "primary": True},
    "gen4": {"label": "第4代 · 雙向旋轉水晶球", "blurb": "2010-11-09 至 2026-05-02", "start": date(2010, 11, 9), "end": date(2026, 5, 5), "primary": False},
    "gen3": {"label": "第3代 · 風車／跑輪", "blurb": "1995–2010", "start": date(1995, 1, 1), "end": date(2010, 11, 9), "primary": False},
    "gen2": {"label": "第2代 · 氣流漏斗", "blurb": "1990–1994", "start": date(1990, 1, 1), "end": date(1995, 1, 1), "primary": False},
    "gen1": {"label": "第1代 · 水晶球", "blurb": "1975/76–1989", "start": date(1975, 1, 1), "end": date(1990, 1, 1), "primary": False},
}
GEN5_START = GENS["gen5"]["start"]
TAB_ORDER = ["gen5", "gen4", "gen3", "gen2", "gen1", "all"]
ERAS = {k: GENS[k]["label"] for k in ("gen5", "gen4", "gen3", "gen2", "gen1")}
ERAS["all"] = "全部歷史（對照）"

def parse_date(s):
    raw = (s or "")[:10]
    if len(raw) < 10:
        return None
    try:
        y, m, d = raw.split("-")
        return date(int(y), int(m), int(d))
    except ValueError:
        return None

def generation_of(d):
    dt = parse_date(d.date)
    if dt is None:
        return None
    for key, meta in GENS.items():
        start, end = meta["start"], meta["end"]
        if dt >= start and (end is None or dt < end):
            return key
    return None

def filter_era(draws, era="gen5"):
    if era == "all":
        return list(draws)
    if era not in GENS:
        return []
    return [d for d in draws if generation_of(d) == era]

def pick_working_set(draws, era="gen5", min_draws=12):
    sliced = filter_era(draws, era)
    if len(sliced) >= min_draws:
        return sliced, era
    if era != "all" and len(draws) >= min_draws:
        return list(draws), "all_fallback"
    return sliced, era
