from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from marksix_rd.ingest import load_csv
from marksix_rd.schema import BALL_COLOR, RED
from marksix_rd.strategies import STRATEGIES, all_tickets


def draws():
    return load_csv(ROOT / "data" / "sample_draws.csv")


def test_official_red_includes_1_and_45():
    assert 1 in RED and 45 in RED
    assert BALL_COLOR[3] == "blue"
    assert BALL_COLOR[49] == "green"


def test_all_named_strategies_emit_valid_tickets():
    d = draws()
    assert set(STRATEGIES) >= {"ensemble", "sklearn_rank", "pair_affinity"}
    for t in all_tickets(d, seed=7):
        assert len(t["mains"]) == 6
        assert len(set(t["mains"])) == 6
        assert t["special"] not in t["mains"]
        assert 1 <= t["special"] <= 49
