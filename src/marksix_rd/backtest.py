"""Walk-forward backtest vs random baseline."""

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
        rows.append(score(ticket["mains"], ticket["special"], actual))
    n_obs = len(rows)
    mean = sum(r["mains_hit"] for r in rows) / n_obs if rows else 0.0
    special_rate = sum(r["special_hit"] for r in rows) / n_obs if rows else 0.0
    if n_obs >= 2:
        var = sum((r["mains_hit"] - mean) ** 2 for r in rows) / (n_obs - 1)
        se = (var / n_obs) ** 0.5
    else:
        var, se = 0.0, 0.0
    z = 1.96
    ci_lo, ci_hi = mean - z * se, mean + z * se
    mu = 6 * 6 / 49
    if n_obs < 8:
        vs = "insufficient_sample"
    elif ci_lo > mu:
        vs = "above_random"
    elif ci_hi < mu:
        vs = "below_random"
    else:
        vs = "undistinguished_from_random"
    return {
        "strategy": strategy,
        "n": n_obs,
        "mean_mains_hit": mean,
        "special_hit_rate": special_rate,
        "var_mains_hit": var,
        "se_mains_hit": se,
        "ci95_mains_hit": [ci_lo, ci_hi],
        "random_expected_mains_hit": mu,
        "random_expected_special": 1 / 49,
        "vs_random": vs,
    }


def compare_all(draws: list[Draw], min_history: int = 20) -> list[dict]:
    return [walk_forward(draws, name, min_history=min_history) for name in STRATEGIES]
