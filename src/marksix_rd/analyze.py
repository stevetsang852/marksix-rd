from __future__ import annotations
from collections import Counter
from typing import Any
from .schema import BALL_COLOR, Draw, zodiac_for

def frequency(draws, include_special=True):
    c = Counter()
    for d in draws:
        c.update(d.mains)
        if include_special:
            c[d.special] += 1
    return dict(c)

def gaps(draws):
    last_seen = {}
    for i, d in enumerate(draws):
        for n in list(d.mains) + [d.special]:
            last_seen[n] = i
    end = len(draws) - 1
    return {n: end - last_seen[n] if n in last_seen else end + 1 for n in range(1, 50)}

def color_counts(draws):
    c = Counter()
    for d in draws:
        for n in list(d.mains) + [d.special]:
            c[BALL_COLOR[n]] += 1
    return dict(c)

def odd_even_profile(draws):
    odd = even = 0
    for d in draws:
        for n in d.mains:
            if n % 2:
                odd += 1
            else:
                even += 1
    total = max(odd + even, 1)
    return {"odd": odd / total, "even": even / total}

def chi_square_vs_uniform(draws, include_special=True):
    freq = frequency(draws, include_special=include_special)
    total = sum(freq.get(n, 0) for n in range(1, 50))
    if total <= 0:
        return {"chi2": 0.0, "df": 48.0, "n_balls": 0.0}
    expected = total / 49.0
    chi2 = sum((freq.get(n, 0) - expected) ** 2 / expected for n in range(1, 50))
    return {"chi2": chi2, "df": 48.0, "n_balls": float(total), "expected": expected}

def summary(draws, year=2026):
    freq = frequency(draws)
    g = gaps(draws)
    return {
        "n_draws": len(draws),
        "latest": draws[-1].to_dict() if draws else None,
        "hot": sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:12],
        "cold_by_gap": sorted(g.items(), key=lambda kv: (-kv[1], kv[0]))[:12],
        "colors": color_counts(draws),
        "odd_even": odd_even_profile(draws),
        "zodiac_sample": {n: zodiac_for(n, year) for n in range(1, 13)},
        "chi2_uniform": chi_square_vs_uniform(draws),
    }
