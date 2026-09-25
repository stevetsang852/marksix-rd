from __future__ import annotations

from collections import Counter
from typing import Any

from .schema import BALL_COLOR, Draw, zodiac_for


def frequency(draws: list[Draw], include_special: bool = True) -> dict[int, int]:
    c: Counter[int] = Counter()
    for d in draws:
        c.update(d.mains)
        if include_special:
            c[d.special] += 1
    return dict(c)


def gaps(draws: list[Draw]) -> dict[int, int]:
    last_seen: dict[int, int] = {}
    for i, d in enumerate(draws):
        for n in list(d.mains) + [d.special]:
            last_seen[n] = i
    end = len(draws) - 1
    return {n: end - last_seen[n] if n in last_seen else end + 1 for n in range(1, 50)}


def color_counts(draws: list[Draw]) -> dict[str, int]:
    c: Counter[str] = Counter()
    for d in draws:
        for n in list(d.mains) + [d.special]:
            c[BALL_COLOR[n]] += 1
    return dict(c)


def odd_even_profile(draws: list[Draw]) -> dict[str, float]:
    odd = even = 0
    for d in draws:
        for n in d.mains:
            if n % 2:
                odd += 1
            else:
                even += 1
    total = max(odd + even, 1)
    return {"odd": odd / total, "even": even / total}


def summary(draws: list[Draw], year: int = 2026) -> dict[str, Any]:
    freq = frequency(draws)
    g = gaps(draws)
    hot = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:12]
    cold = sorted(g.items(), key=lambda kv: (-kv[1], kv[0]))[:12]
    return {
        "n_draws": len(draws),
        "latest": draws[-1].to_dict() if draws else None,
        "hot": hot,
        "cold_by_gap": cold,
        "colors": color_counts(draws),
        "odd_even": odd_even_profile(draws),
        "zodiac_sample": {n: zodiac_for(n, year) for n in range(1, 13)},
    }
