from __future__ import annotations
from datetime import date
from .schema import Draw

GEN5_START = date(2026, 5, 5)
ERAS = {
    "gen5": "第5代攪珠機（2026-05-05 起）",
    "pre_gen5": "第5代之前",
    "all": "全部歷史（對照）",
}

def parse_date(s: str):
    raw = (s or "")[:10]
    if len(raw) < 10:
        return None
    try:
        y, m, d = raw.split("-")
        return date(int(y), int(m), int(d))
    except ValueError:
        return None

def filter_era(draws, era="gen5"):
    if era == "all":
        return list(draws)
    out = []
    for d in draws:
        dt = parse_date(d.date)
        if dt is None:
            continue
        if era == "gen5" and dt >= GEN5_START:
            out.append(d)
        elif era == "pre_gen5" and dt < GEN5_START:
            out.append(d)
    return out

def pick_working_set(draws, era="gen5", min_draws=12):
    sliced = filter_era(draws, era)
    if len(sliced) >= min_draws:
        return sliced, era
    if era != "all" and len(draws) >= min_draws:
        return list(draws), "all_fallback"
    return sliced, era
