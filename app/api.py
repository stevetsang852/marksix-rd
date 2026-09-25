"""HTTP API for dashboard, Grok bots, and other agents."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from marksix_rd.analyze import summary
from marksix_rd.backtest import compare_all, walk_forward
from marksix_rd.era import filter_era
from marksix_rd.ingest import load_processed
from marksix_rd.predict_service import prediction_payload, strategies_catalog
from marksix_rd.strategies import STRATEGIES

app = FastAPI(
    title="marksix-rd",
    version="0.2.0",
    description="Mark Six research API. Predictions are lab tickets, not advice.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    draws = load_processed()
    return {"ok": True, "n_draws": len(draws)}


@app.get("/v1/strategies")
def list_strategies():
    """Catalog of strategy names + plain-language logic."""
    return strategies_catalog()


@app.get("/v1/predictions")
def predictions(
    era: str = Query("gen5", description="gen5|gen4|gen3|gen2|gen1|all"),
    seed: int = Query(42, ge=1, le=99999),
    strategy: str | None = Query(None, description="optional single strategy name"),
):
    """All (or one) research tickets for the requested machine era."""
    if strategy and strategy.lower() not in STRATEGIES:
        raise HTTPException(status_code=400, detail=f"unknown strategy: {strategy}")
    return prediction_payload(era=era, seed=seed, strategy=strategy)


@app.get("/v1/predictions/{strategy}")
def prediction_one(
    strategy: str,
    era: str = Query("gen5"),
    seed: int = Query(42, ge=1, le=99999),
):
    if strategy.lower() not in STRATEGIES:
        raise HTTPException(status_code=400, detail=f"unknown strategy: {strategy}")
    return prediction_payload(era=era, seed=seed, strategy=strategy)


@app.get("/v1/backtest")
def backtest_v1(
    era: str = Query("gen5"),
    strategy: str | None = Query(None),
    min_history: int = Query(20, ge=8, le=200),
):
    draws = load_processed()
    sliced = draws if era == "all" else filter_era(draws, era)
    if len(sliced) < min_history + 2:
        sliced = draws
    if strategy:
        if strategy not in STRATEGIES:
            raise HTTPException(status_code=400, detail=f"unknown strategy: {strategy}")
        return {"ok": True, "era": era, "results": [walk_forward(sliced, strategy, min_history=min_history)]}
    return {"ok": True, "era": era, "results": compare_all(sliced, min_history=min_history)}


@app.get("/draws")
def draws(limit: int = 30):
    data = load_processed()
    return [d.to_dict() for d in data[-limit:]]


@app.get("/summary")
def get_summary():
    return summary(load_processed())


@app.get("/tickets")
def tickets(seed: int = 42, era: str = "gen5"):
    return prediction_payload(era=era, seed=seed)


@app.get("/backtest")
def backtest():
    return compare_all(load_processed())
