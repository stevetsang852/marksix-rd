from __future__ import annotations

from typing import Callable

from .schema import Draw
from .strategies import STRATEGIES


def score(pred_mains: list[int], pred_special: int, actual: Draw) -> dict:
    mains_hit = len(set(pred_mains) & set(actual.mains))
    return {
        "mains_hit": mains_hit,
        "special_hit": int(pred_special == actual.special),
        "any_special_in_mains": int(actual.special in pred_mains),
    }


def walk_forward(
    draws: list[Draw],
    strategy: str = "hot",
    min_history: int = 30,
    seed: int = 42,
) -> dict:
    fn: Callable = STRATEGIES[strategy]
    rows = []
    for i in range(min_history, len(draws)):
        hist = draws[:i]
        actual = draws[i]
        ticket = fn(hist, seed=seed + i)
        s = score(ticket["mains"], ticket["special"], actual)
        rows.append(s)
    n = max(len(rows), 1)
    return {
        "strategy": strategy,
        "n": len(rows),
        "mean_mains_hit": sum(r["mains_hit"] for r in rows) / n if rows else 0.0,
        "special_hit_rate": sum(r["special_hit"] for r in rows) / n if rows else 0.0,
        "random_expected_mains_hit": 6 * 6 / 49,
        "random_expected_special": 1 / 49,
    }


def compare_all(draws: list[Draw], min_history: int = 20) -> list[dict]:
    return [walk_forward(draws, name, min_history=min_history) for name in STRATEGIES]
