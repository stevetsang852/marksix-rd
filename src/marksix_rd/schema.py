from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class Draw:
    issue: str
    date: str
    n1: int
    n2: int
    n3: int
    n4: int
    n5: int
    n6: int
    special: int
    source: str = "unknown"

    @property
    def mains(self) -> tuple[int, ...]:
        return tuple(sorted((self.n1, self.n2, self.n3, self.n4, self.n5, self.n6)))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["mains"] = list(self.mains)
        return d


BALL_COLOR = {}
for n in range(1, 50):
    r = n % 3
    BALL_COLOR[n] = {1: "red", 2: "blue", 0: "green"}[r]


ZODIAC_CYCLE = [
    "蛇", "龍", "兔", "虎", "牛", "鼠", "豬", "狗", "雞", "猴", "羊", "馬",
]


def zodiac_for(n: int, year: int = 2026) -> str:
    offset = (2025 - year) % 12
    idx = (n - 1 + offset) % 12
    return ZODIAC_CYCLE[idx]
