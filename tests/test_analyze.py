from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from marksix_rd.analyze import frequency, summary
from marksix_rd.backtest import compare_all, score
from marksix_rd.ingest import load_csv, parse_history_csv_bytes, parse_hkjc_last30
from marksix_rd.schema import Draw
from marksix_rd.strategies import all_tickets


def sample_draws():
    return load_csv(ROOT / "data" / "sample_draws.csv", source="sample")


def test_csv_loads():
    draws = sample_draws()
    assert len(draws) >= 30
    assert all(1 <= n <= 49 for d in draws for n in d.mains)


def test_frequency_covers_range():
    freq = frequency(sample_draws())
    assert min(freq) >= 1 and max(freq) <= 49


def test_tickets_unique_six():
    for t in all_tickets(sample_draws()):
        assert len(set(t["mains"])) == 6
        assert t["special"] not in t["mains"]


def test_score_perfect():
    d = Draw("x", "2025-01-01", 1, 2, 3, 4, 5, 6, 7)
    s = score([1, 2, 3, 4, 5, 6], 7, d)
    assert s["mains_hit"] == 6 and s["special_hit"] == 1


def test_backtest_runs():
    rows = compare_all(sample_draws(), min_history=10)
    assert {r["strategy"] for r in rows} >= {"random", "hot"}


def test_parse_list_shape():
    raw = [{"id": "26/001", "date": "2026-01-03", "n1": 1, "n2": 2, "n3": 3, "n4": 4, "n5": 5, "n6": 6, "specialNumber": 7}]
    draws = parse_hkjc_last30(raw)
    assert draws[0].special == 7


def test_parse_history_csv_shape():
    raw = b"draw,date,weekday,no1,no2,no3,no4,no5,no6,special\n02/053,2002-07-04,Thu,1,2,3,4,5,6,7\n"
    draws = parse_history_csv_bytes(raw)
    assert draws[0].issue == "02/053"
    assert draws[0].date == "2002-07-04"
    assert draws[0].mains == (1, 2, 3, 4, 5, 6)
    assert draws[0].special == 7


def test_summary_latest():
    s = summary(sample_draws())
    assert s["latest"]["issue"] == "25/035"
