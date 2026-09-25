"""Stable prediction payload for bots / other agents."""

from __future__ import annotations

from typing import Any

from .era import ERAS, TAB_ORDER, filter_era
from .ingest import load_processed
from .schema import Draw
from .strategies import PLAIN_LOGIC, STRATEGIES, all_tickets


def _draw_brief(d: Draw) -> dict[str, Any]:
    return {
        "issue": d.issue,
        "date": d.date,
        "mains": list(d.mains),
        "special": d.special,
        "source": d.source,
    }


def resolve_window(draws: list[Draw], era: str = "gen5", min_n: int = 8) -> tuple[list[Draw], str, bool]:
    key = (era or "gen5").lower()
    if key not in TAB_ORDER:
        key = "gen5"
    sliced = draws if key == "all" else filter_era(draws, key)
    fallback = False
    if len(sliced) < min_n:
        sliced = draws
        fallback = True
    return sliced, key, fallback


def prediction_payload(
    era: str = "gen5",
    seed: int = 42,
    strategy: str | None = None,
    draws: list[Draw] | None = None,
) -> dict[str, Any]:
    draws = draws if draws is not None else load_processed()
    window, era_key, fallback = resolve_window(draws, era)
    tickets = all_tickets(window, seed=seed)
    if strategy:
        name = strategy.lower()
        tickets = [t for t in tickets if t["name"] == name]
        if not tickets and name in STRATEGIES:
            tickets = [STRATEGIES[name](window, seed=seed)]
    last = window[-1] if window else None
    return {
        "ok": True,
        "disclaimer": "research-only; Mark Six is a negative-expectation game; not betting advice",
        "era": era_key,
        "era_label": ERAS.get(era_key, era_key),
        "used_all_draws_fallback": fallback,
        "n_draws": len(window),
        "seed": int(seed),
        "as_of": _draw_brief(last) if last else None,
        "tickets": tickets,
        "logic": {t["name"]: PLAIN_LOGIC.get(t["name"], "") for t in tickets},
    }


def strategies_catalog() -> dict[str, Any]:
    return {
        "ok": True,
        "primary_era": "gen5",
        "eras": TAB_ORDER,
        "strategies": [
            {"name": name, "logic": PLAIN_LOGIC.get(name, "")} for name in STRATEGIES
        ],
    }
