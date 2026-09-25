"""Research ticket generators. Not betting advice."""
from __future__ import annotations
import random
from collections import Counter
from typing import Callable
import numpy as np
from .features import number_features
from .schema import BALL_COLOR, Draw

def _finish(name, mains, special, note=""):
    mains = sorted(int(x) for x in mains)
    special = int(special)
    if special in mains:
        special = next(n for n in range(1, 50) if n not in mains)
    return {"name": name, "mains": mains, "special": special, "note": note,
            "colors": [BALL_COLOR[n] for n in mains],
            "odd": sum(n % 2 for n in mains), "high": sum(1 for n in mains if n >= 25)}

def _weighted_sample(weights, k, rng):
    pool = list(range(1, 50))
    pool_w = [max(float(weights.get(n, 0.0)), 1e-9) for n in pool]
    picked = []
    for _ in range(k):
        total = sum(pool_w)
        r = rng.random() * total
        acc = 0.0
        idx = 0
        for i, ww in enumerate(pool_w):
            acc += ww
            if acc >= r:
                idx = i
                break
        picked.append(pool.pop(idx))
        pool_w.pop(idx)
    return picked

def strategy_random(draws, seed=42):
    rng = random.Random(seed)
    mains = sorted(rng.sample(range(1, 50), 6))
    special = rng.choice([n for n in range(1, 50) if n not in mains])
    return _finish("random", mains, special, "uniform baseline")

def strategy_hot(draws, seed=42):
    c = Counter()
    for d in draws:
        c.update(d.all_seven())
    ranked = [n for n, _ in c.most_common()] or list(range(1, 50))
    rng = random.Random(seed)
    mains = sorted(rng.sample(ranked[:18], 6))
    special = next((n for n in ranked if n not in mains), 1)
    return _finish("hot", mains, special, "highest historical frequency")

def strategy_cold(draws, seed=42):
    last = {n: -1 for n in range(1, 50)}
    for i, d in enumerate(draws):
        for n in d.all_seven():
            last[n] = i
    gap = {n: len(draws) - 1 - last[n] for n in range(1, 50)}
    ranked = sorted(gap, key=lambda n: (-gap[n], n))
    rng = random.Random(seed)
    mains = sorted(rng.sample(ranked[:18], 6))
    special = next(n for n in ranked if n not in mains)
    return _finish("cold", mains, special, "longest absence (overdue)")

def strategy_balanced(draws, seed=42):
    hot = strategy_hot(draws, seed)
    cold = strategy_cold(draws, seed + 1)
    rng = random.Random(seed)
    pool = list(dict.fromkeys(hot["mains"] + cold["mains"]))
    while len(pool) < 12:
        pool.append(rng.randint(1, 49))
        pool = list(dict.fromkeys(pool))
    mains = sorted(rng.sample(pool[:12], 6))
    special = hot["special"] if hot["special"] not in mains else cold["special"]
    return _finish("balanced", mains, special, "mix hot + cold pool")

def strategy_color_spread(draws, seed=42):
    rng = random.Random(seed)
    by = {"red": [], "blue": [], "green": []}
    for n in range(1, 50):
        by[BALL_COLOR[n]].append(n)
    mains = []
    for col in ("red", "blue", "green"):
        mains.extend(rng.sample(by[col], 2))
    special = rng.choice([n for n in range(1, 50) if n not in mains])
    return _finish("color_spread", mains, special, "2 red + 2 blue + 2 green")

def strategy_sum_band(draws, seed=42):
    rng = random.Random(seed)
    sums = [sum(d.mains) for d in draws] or [150]
    target = float(np.median(sums))
    best = sorted(rng.sample(range(1, 50), 6))
    best_err = abs(sum(best) - target)
    for _ in range(80):
        cand = sorted(rng.sample(range(1, 50), 6))
        err = abs(sum(cand) - target)
        if err < best_err:
            best_err, best = err, cand
    special = rng.choice([n for n in range(1, 50) if n not in best])
    return _finish("sum_band", best, special, f"target sum ≈ {target:.0f}")

def strategy_pair_affinity(draws, seed=42):
    pair = Counter()
    for d in draws:
        m = d.mains
        for i in range(6):
            for j in range(i + 1, 6):
                pair[(m[i], m[j])] += 1
    rng = random.Random(seed)
    if not pair:
        return strategy_random(draws, seed)
    (a, b), _ = pair.most_common(1)[0]
    chosen = {a, b}
    while len(chosen) < 6:
        scores = Counter()
        for n in range(1, 50):
            if n in chosen:
                continue
            scores[n] = sum(pair.get(tuple(sorted((n, x))), 0) for x in chosen)
        pool = [n for n, _ in scores.most_common(8)] or [n for n in range(1, 50) if n not in chosen]
        chosen.add(rng.choice(pool))
    mains = sorted(chosen)
    special = rng.choice([n for n in range(1, 50) if n not in mains])
    return _finish("pair_affinity", mains, special, "grow from most common pair")

def strategy_exp_smooth(draws, seed=42):
    feats = number_features(draws)
    rec = feats[:, 2]
    w = {n: float(rec[n - 1]) for n in range(1, 50)}
    rng = random.Random(seed)
    mains = sorted(_weighted_sample(w, 6, rng))
    special = max((n for n in range(1, 50) if n not in mains), key=lambda n: w[n])
    return _finish("exp_smooth", mains, special, "exponential recency weights")

def strategy_sklearn_rank(draws, seed=42):
    if len(draws) < 16:
        t = strategy_hot(draws, seed)
        t["name"] = "sklearn_rank"
        t["note"] = "fallback hot (history too short)"
        return t
    xs, ys = [], []
    for t in range(8, len(draws)):
        xs.append(number_features(draws[:t]))
        lab = np.zeros(49)
        for n in draws[t].all_seven():
            lab[n - 1] = 1.0
        ys.append(lab)
    Xtr, ytr = np.vstack(xs), np.concatenate(ys)
    try:
        from sklearn.linear_model import Ridge
        model = Ridge(alpha=2.0)
        model.fit(Xtr, ytr)
        scores = model.predict(number_features(draws))
        note = "Ridge rank on freq/gap/recency"
    except Exception:
        eye = np.eye(Xtr.shape[1])
        beta = np.linalg.pinv(Xtr.T @ Xtr + 2.0 * eye) @ Xtr.T @ ytr
        scores = number_features(draws) @ beta
        note = "numpy ridge rank on freq/gap/recency"
    ranked = list(np.argsort(-scores) + 1)
    mains = sorted(int(n) for n in ranked[:6])
    special = int(next(n for n in ranked[6:] if n not in mains))
    return _finish("sklearn_rank", mains, special, note)

def strategy_ensemble(draws, seed=42):
    votes, specials = Counter(), Counter()
    for fn in (strategy_hot, strategy_cold, strategy_balanced, strategy_exp_smooth, strategy_pair_affinity, strategy_sklearn_rank):
        t = fn(draws, seed)
        votes.update(t["mains"])
        specials[t["special"]] += 1
    mains = [n for n, _ in votes.most_common(6)]
    special = next((n for n, _ in specials.most_common() if n not in mains), 1)
    return _finish("ensemble", mains, special, "vote across 6 research strategies")

STRATEGIES = {
    "random": strategy_random,
    "hot": strategy_hot,
    "cold": strategy_cold,
    "balanced": strategy_balanced,
    "color_spread": strategy_color_spread,
    "sum_band": strategy_sum_band,
    "pair_affinity": strategy_pair_affinity,
    "exp_smooth": strategy_exp_smooth,
    "sklearn_rank": strategy_sklearn_rank,
    "ensemble": strategy_ensemble,
}

def all_tickets(draws, seed=42):
    return [fn(draws, seed=seed) for fn in STRATEGIES.values()]
