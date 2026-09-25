"""Honest chance numbers and history match for a 6-from-49 ticket."""

from __future__ import annotations

from math import comb
from typing import Any

POOL = 49
PICK = 6
DEN = comb(POOL, PICK)


def mains_hit_pmf() -> dict[int, float]:
    return {k: comb(PICK, k) * comb(POOL - PICK, PICK - k) / DEN for k in range(PICK + 1)}


def ticket_chance() -> dict[str, Any]:
    pmf = mains_hit_pmf()
    return {
        "model": "hypergeometric_6_of_49",
        "same_for_every_ticket": True,
        "expected_mains_hit": PICK * PICK / POOL,
        "p_special": 1 / POOL,
        "p_mains_exact": {str(k): pmf[k] for k in range(PICK + 1)},
        "p_mains_at_least": {str(k): sum(pmf[i] for i in range(k, PICK + 1)) for k in range(PICK + 1)},
        "p_jackpot": pmf[6],
        "note": "If draws are uniform, every 6-number ticket has these probabilities.",
    }


def match_history(mains: list[int], special: int, draws: list) -> dict[str, Any]:
    target = frozenset(int(n) for n in mains)
    spec = int(special)
    exact_mains: list[dict] = []
    exact_seven: list[dict] = []
    scored: list[dict] = []
    for d in draws:
        hit = len(target & set(d.mains))
        rec = {
            "issue": d.issue,
            "date": d.date,
            "mains": list(d.mains),
            "special": d.special,
            "mains_hit": hit,
            "special_hit": int(d.special == spec),
        }
        scored.append(rec)
        if hit == 6:
            exact_mains.append(rec)
            if d.special == spec:
                exact_seven.append(rec)
    scored.sort(key=lambda r: (-r["mains_hit"], -r["special_hit"], r["date"]))
    best = scored[0] if scored else None
    return {
        "appeared_before": bool(exact_mains),
        "appeared_before_with_special": bool(exact_seven),
        "exact_mains_draws": exact_mains,
        "exact_seven_draws": exact_seven,
        "best_mains_hit": best["mains_hit"] if best else 0,
        "nearest": scored[:3],
    }


def attach_chance(
    ticket: dict[str, Any],
    walk: dict[str, Any] | None = None,
    draws: list | None = None,
) -> dict[str, Any]:
    out = dict(ticket)
    out["chance"] = ticket_chance()
    if walk:
        out["walk_forward"] = {
            "n": walk.get("n", 0),
            "mean_mains_hit": walk.get("mean_mains_hit"),
            "ci95_mains_hit": walk.get("ci95_mains_hit"),
            "special_hit_rate": walk.get("special_hit_rate"),
            "vs_random": walk.get("vs_random"),
            "random_expected_mains_hit": walk.get("random_expected_mains_hit"),
        }
    if draws is not None:
        out["history"] = match_history(ticket["mains"], ticket["special"], draws)
    return out
