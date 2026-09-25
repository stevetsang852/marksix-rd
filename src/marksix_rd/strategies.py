from __future__ import annotations

import random
from typing import Sequence

from .analyze import frequency, gaps
from .schema import Draw


def _pick(pool: Sequence[int], k: int, rng: random.Random) -> list[int]:
    uniq = list(dict.fromkeys(int(x) for x in pool if 1 <= int(x) <= 49))
    if len(uniq) < k:
        rest = [n for n in range(1, 50) if n not in uniq]
        rng.shuffle(rest)
        uniq.extend(rest)
    return sorted(rng.sample(uniq, k))


def strategy_random(draws: list[Draw], seed: int = 42) -> dict:
    rng = random.Random(seed)
    mains = sorted(rng.sample(range(1, 50), 6))
    special = rng.choice([n for n in range(1, 50) if n not in mains])
    return {"name": "random", "mains": mains, "special": special}


def strategy_hot(draws: list[Draw], seed: int = 42) -> dict:
    freq = frequency(draws)
    ranked = [n for n, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))]
    rng = random.Random(seed)
    mains = _pick(ranked[:18], 6, rng)
    special = next((n for n in ranked if n not in mains), rng.randint(1, 49))
    return {"name": "hot", "mains": mains, "special": special}


def strategy_cold(draws: list[Draw], seed: int = 42) -> dict:
    g = gaps(draws)
    ranked = [n for n, _ in sorted(g.items(), key=lambda kv: (-kv[1], kv[0]))]
    rng = random.Random(seed)
    mains = _pick(ranked[:18], 6, rng)
    special = next((n for n in ranked if n not in mains), rng.randint(1, 49))
    return {"name": "cold", "mains": mains, "special": special}


def strategy_balanced(draws: list[Draw], seed: int = 42) -> dict:
    freq = frequency(draws)
    g = gaps(draws)
    hot = [n for n, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))]
    cold = [n for n, _ in sorted(g.items(), key=lambda kv: (-kv[1], kv[0]))]
    rng = random.Random(seed)
    pool = hot[:9] + cold[:9]
    mains = _pick(pool, 6, rng)
    special = next((n for n in hot + cold if n not in mains), rng.randint(1, 49))
    return {"name": "balanced", "mains": mains, "special": special}


STRATEGIES = {
    "random": strategy_random,
    "hot": strategy_hot,
    "cold": strategy_cold,
    "balanced": strategy_balanced,
}


def all_tickets(draws: list[Draw], seed: int = 42) -> list[dict]:
    return [fn(draws, seed=seed) for fn in STRATEGIES.values()]
