from __future__ import annotations

import numpy as np

from .schema import BALL_COLOR, Draw


def number_features(draws: list[Draw]) -> np.ndarray:
    n_draw = len(draws)
    freq = np.zeros(50, dtype=float)
    last = np.full(50, n_draw, dtype=float)
    recency_decay = np.zeros(50, dtype=float)
    for i, d in enumerate(draws):
        w = 0.97 ** (n_draw - 1 - i)
        for n in d.all_seven():
            freq[n] += 1
            last[n] = i
            recency_decay[n] += w
    gap = (n_draw - 1) - last
    gap[last >= n_draw] = n_draw
    odd = np.array([n % 2 for n in range(50)], dtype=float)
    high = np.array([1.0 if n >= 25 else 0.0 for n in range(50)])
    color_code = np.zeros(50, dtype=float)
    for n in range(1, 50):
        color_code[n] = {"red": 0.0, "blue": 1.0, "green": 2.0}[BALL_COLOR[n]]
    freq_n = freq / max(n_draw, 1)
    gap_n = gap / max(n_draw, 1)
    rec_n = recency_decay / max(recency_decay.max(), 1e-9)
    feats = np.stack([freq_n, gap_n, rec_n, odd, high, color_code / 2.0], axis=1)
    return feats[1:]
