from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

RED = {1, 2, 7, 8, 12, 13, 18, 19, 23, 24, 29, 30, 34, 35, 40, 45, 46}
BLUE = {3, 4, 9, 10, 14, 15, 20, 25, 26, 31, 36, 37, 41, 42, 47, 48}
GREEN = {5, 6, 11, 16, 17, 21, 22, 27, 28, 32, 33, 38, 39, 43, 44, 49}

BALL_COLOR: dict[int, str] = {}
for n in range(1, 50):
    if n in RED:
        BALL_COLOR[n] = "red"
    elif n in BLUE:
        BALL_COLOR[n] = "blue"
    else:
        BALL_COLOR[n] = "green"

ZODIAC_CYCLE = ["蛇", "龍", "兔", "虎", "牛", "鼠", "豬", "狗", "雞", "猴", "羊", "馬"]


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

    def all_seven(self) -> tuple[int, ...]:
        return self.mains + (self.special,)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["mains"] = list(self.mains)
        d["colors"] = [BALL_COLOR[n] for n in self.mains]
        return d


def zodiac_for(n: int, year: int = 2026) -> str:
    offset = (2025 - year) % 12
    return ZODIAC_CYCLE[(n - 1 + offset) % 12]


def color_of(n: int) -> str:
    return BALL_COLOR[int(n)]
