from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from marksix_rd.analyze import summary
from marksix_rd.backtest import compare_all
from marksix_rd.ingest import load_processed
from marksix_rd.strategies import all_tickets

app = FastAPI(title="marksix-rd", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/draws")
def draws(limit: int = 30):
    return load_processed()[-limit:]


@app.get("/summary")
def get_summary():
    return summary(load_processed())


@app.get("/tickets")
def tickets(seed: int = 42):
    return all_tickets(load_processed(), seed=seed)


@app.get("/backtest")
def backtest():
    return compare_all(load_processed())
