"""Stable prediction payload for bots / other agents."""

from __future__ import annotations

import secrets
from typing import Any

from .backtest import walk_forward
from .chance import attach_chance, ticket_chance
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


def _normalize_strategy(strategy: str | None) -> str:
    name = (strategy or "all").strip().lower()
    if name in {"", "all", "*"}:
        return "all"
    return name


def known_strategy(strategy: str | None) -> bool:
    name = _normalize_strategy(strategy)
    return name == "all" or name in STRATEGIES


def new_seed() -> int:
    return secrets.randbelow(99999) + 1


def resolve_request_seed(explicit: int | None = None) -> tuple[int, bool]:
    if explicit is None:
        return new_seed(), True
    value = int(explicit)
    if value < 1 or value > 99999:
        return new_seed(), True
    return value, False


def prediction_payload(
    era: str = "gen5",
    seed: int | None = None,
    strategy: str | None = None,
    draws: list[Draw] | None = None,
) -> dict[str, Any]:
    use_seed, generated = resolve_request_seed(seed)
    draws = draws if draws is not None else load_processed()
    window, era_key, fallback = resolve_window(draws, era)
    tickets = all_tickets(window, seed=use_seed)
    selected = _normalize_strategy(strategy)
    if selected != "all":
        tickets = [t for t in tickets if t["name"] == selected]
        if not tickets and selected in STRATEGIES:
            tickets = [STRATEGIES[selected](window, seed=use_seed)]
    min_hist = 20 if len(window) > 28 else max(8, len(window) // 2)
    wf_map: dict[str, dict] = {}
    names = {t["name"] for t in tickets}
    for name in names:
        if name in STRATEGIES:
            wf_map[name] = walk_forward(window, name, min_history=min_hist, seed=use_seed)
    tickets = [attach_chance(t, wf_map.get(t["name"]), draws) for t in tickets]
    last = window[-1] if window else None
    payload: dict[str, Any] = {
        "ok": True,
        "disclaimer": "research-only; Mark Six is a negative-expectation game; not betting advice",
        "era": era_key,
        "era_label": ERAS.get(era_key, era_key),
        "used_all_draws_fallback": fallback,
        "n_draws": len(window),
        "seed": use_seed,
        "seed_generated": generated,
        "strategy": selected,
        "as_of": _draw_brief(last) if last else None,
        "tickets": tickets,
        "chance_legend": ticket_chance(),
        "logic": {t["name"]: PLAIN_LOGIC.get(t["name"], "") for t in tickets},
    }
    if selected != "all" and tickets:
        payload["ticket"] = tickets[0]
    return payload


def strategies_catalog() -> dict[str, Any]:
    return {
        "ok": True,
        "primary_era": "gen5",
        "eras": TAB_ORDER,
        "strategies": [{"name": name, "logic": PLAIN_LOGIC.get(name, "")} for name in STRATEGIES],
    }
