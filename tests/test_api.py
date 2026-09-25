from fastapi.testclient import TestClient

from app.api import app
from marksix_rd.predict_service import prediction_payload, strategies_catalog
from marksix_rd.schema import Draw
from marksix_rd.strategies import STRATEGIES


def _toy(n: int = 12) -> list[Draw]:
    rows = []
    for i in range(n):
        base = [(i + k) % 49 + 1 for k in range(6)]
        special = (i + 20) % 49 + 1
        if special in base:
            special = next(x for x in range(1, 50) if x not in base)
        rows.append(
            Draw(
                issue=f"t/{i:03d}",
                date=f"2026-06-{(i % 28) + 1:02d}",
                n1=base[0],
                n2=base[1],
                n3=base[2],
                n4=base[3],
                n5=base[4],
                n6=base[5],
                special=special,
                source="test",
            )
        )
    return rows


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_v1_strategies_catalog():
    r = client.get("/v1/strategies")
    assert r.status_code == 200
    body = r.json()
    names = {s["name"] for s in body["strategies"]}
    assert names == set(STRATEGIES)
    assert body["primary_era"] == "gen5"


def test_v1_predictions_shape():
    r = client.get("/v1/predictions", params={"era": "gen5", "seed": 42})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "disclaimer" in body
    assert body["seed"] == 42
    assert len(body["tickets"]) == len(STRATEGIES)
    for t in body["tickets"]:
        assert len(t["mains"]) == 6
        assert len(set(t["mains"])) == 6
        assert t["special"] not in t["mains"]
        assert all(1 <= n <= 49 for n in t["mains"])


def test_v1_predictions_one_strategy():
    r = client.get("/v1/predictions/ensemble", params={"seed": 7})
    assert r.status_code == 200
    tickets = r.json()["tickets"]
    assert len(tickets) == 1
    assert tickets[0]["name"] == "ensemble"


def test_v1_unknown_strategy_400():
    r = client.get("/v1/predictions", params={"strategy": "magic"})
    assert r.status_code == 400


def test_tickets_alias_matches_v1():
    a = client.get("/tickets", params={"seed": 42, "era": "all"}).json()
    b = client.get("/v1/predictions", params={"seed": 42, "era": "all"}).json()
    assert a["tickets"] == b["tickets"]


def test_draws_are_json_dicts():
    r = client.get("/draws", params={"limit": 3})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if data:
        assert "issue" in data[0]
        assert "mains" in data[0]


def test_service_deterministic_on_toy_draws():
    draws = _toy()
    a = prediction_payload(era="all", seed=3, draws=draws)
    b = prediction_payload(era="all", seed=3, draws=draws)
    assert a["tickets"] == b["tickets"]
    catalog = strategies_catalog()
    assert len(catalog["strategies"]) == 10
