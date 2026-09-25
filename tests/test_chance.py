from math import comb

from marksix_rd.chance import mains_hit_pmf, match_history, ticket_chance
from marksix_rd.predict_service import prediction_payload
from marksix_rd.schema import Draw


def test_pmf_sums_to_one():
    pmf = mains_hit_pmf()
    assert abs(sum(pmf.values()) - 1) < 1e-12
    assert abs(pmf[6] - 1 / comb(49, 6)) < 1e-18


def test_ticket_chance_keys():
    c = ticket_chance()
    assert c["same_for_every_ticket"] is True
    assert abs(c["expected_mains_hit"] - 36 / 49) < 1e-12
    assert "3" in c["p_mains_at_least"]


def test_payload_tickets_include_chance():
    draws = []
    for i in range(24):
        base = [(i + k) % 49 + 1 for k in range(6)]
        special = (i + 30) % 49 + 1
        if special in base:
            special = next(x for x in range(1, 50) if x not in base)
        draws.append(
            Draw(
                issue=f"c/{i:03d}",
                date=f"2026-08-{(i % 27) + 1:02d}",
                n1=base[0], n2=base[1], n3=base[2], n4=base[3], n5=base[4], n6=base[5],
                special=special, source="test",
            )
        )
    body = prediction_payload(era="all", seed=9, strategy="hot", draws=draws)
    t = body["ticket"]
    assert "chance" in t and "walk_forward" in t and "history" in t
    assert body["chance_legend"]["p_jackpot"] == t["chance"]["p_jackpot"]


def test_all_tickets_share_same_chance():
    draws = []
    for i in range(16):
        base = [(i + 2 * k) % 49 + 1 for k in range(6)]
        special = (i + 11) % 49 + 1
        if special in base:
            special = next(x for x in range(1, 50) if x not in base)
        draws.append(
            Draw(
                issue=f"d/{i:03d}",
                date=f"2026-08-{(i % 27) + 1:02d}",
                n1=base[0], n2=base[1], n3=base[2], n4=base[3], n5=base[4], n6=base[5],
                special=special, source="test",
            )
        )
    body = prediction_payload(era="all", seed=3, strategy="all", draws=draws)
    assert len(body["tickets"]) == 10
    assert len({t["chance"]["p_jackpot"] for t in body["tickets"]}) == 1
    for t in body["tickets"]:
        assert "history" in t


def test_match_history_detects_exact_past_draw():
    past = Draw("26/001", "2026-05-05", 1, 2, 3, 4, 5, 6, 7, source="t")
    other = Draw("26/002", "2026-05-07", 8, 9, 10, 11, 12, 13, 14, source="t")
    hit = match_history([1, 2, 3, 4, 5, 6], 7, [past, other])
    miss = match_history([1, 2, 3, 4, 5, 8], 7, [past, other])
    assert hit["appeared_before"] is True
    assert hit["appeared_before_with_special"] is True
    assert hit["exact_mains_draws"][0]["issue"] == "26/001"
    assert miss["appeared_before"] is False
    assert miss["best_mains_hit"] == 5
