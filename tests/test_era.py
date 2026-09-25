from datetime import date
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from marksix_rd.era import DISPLAY_TAB_ORDER, GEN5_START, TAB_ORDER, filter_era, generation_of, pick_working_set
from marksix_rd.schema import Draw

def _d(issue, day):
    return Draw(issue, day, 1, 2, 3, 4, 5, 6, 7)

def test_gen5_start_is_2026_may_5():
    assert GEN5_START == date(2026, 5, 5)

def test_tab_order_starts_with_gen5():
    assert TAB_ORDER[0] == "gen5"

def test_display_tab_order_hides_empty_early_generations():
    assert DISPLAY_TAB_ORDER == ["gen5", "gen4", "gen3", "all"]

def test_generation_boundaries():
    assert generation_of(_d("a", "1989-12-31")) == "gen1"
    assert generation_of(_d("d", "2010-11-09")) == "gen4"
    assert generation_of(_d("f", "2026-05-05")) == "gen5"

def test_filter_splits_on_boundary():
    rows = [_d("a", "2026-05-04"), _d("b", "2026-05-05")]
    assert [x.issue for x in filter_era(rows, "gen5")] == ["b"]
    assert [x.issue for x in filter_era(rows, "gen4")] == ["a"]

def test_fallback_when_window_tiny():
    rows = [_d("a", "2025-01-01")] * 20
    sliced, used = pick_working_set(rows, era="gen5", min_draws=12)
    assert used == "all_fallback"
