from datetime import date
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from marksix_rd.era import GEN5_START, filter_era, pick_working_set
from marksix_rd.schema import Draw

def _d(issue, day):
    return Draw(issue, day, 1, 2, 3, 4, 5, 6, 7)

def test_gen5_start_is_2026_may_5():
    assert GEN5_START == date(2026, 5, 5)

def test_filter_splits_on_boundary():
    rows = [_d("a", "2026-05-04"), _d("b", "2026-05-05"), _d("c", "2026-09-24")]
    assert [x.issue for x in filter_era(rows, "gen5")] == ["b", "c"]
    assert [x.issue for x in filter_era(rows, "pre_gen5")] == ["a"]

def test_fallback_when_window_tiny():
    rows = [_d("a", "2025-01-01")] * 20
    sliced, used = pick_working_set(rows, era="gen5", min_draws=12)
    assert used == "all_fallback"
    assert len(sliced) == 20
