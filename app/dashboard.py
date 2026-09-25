from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from marksix_rd.analyze import frequency, summary
from marksix_rd.backtest import compare_all
from marksix_rd.era import ERAS, GEN5_START, pick_working_set
from marksix_rd.ingest import load_processed
from marksix_rd.schema import BALL_COLOR
from marksix_rd.strategies import STRATEGIES, all_tickets

st.set_page_config(page_title="Mark Six R&D Lab", layout="wide")
st.markdown('''<style>
.ball {display:inline-flex;align-items:center;justify-content:center;width:42px;height:42px;border-radius:50%;margin:0 4px;color:#fff;font-weight:700;}
.ball.red {background:#d32f2f;} .ball.blue {background:#1565c0;} .ball.green {background:#2e7d32;}
.ball.special {outline:3px solid #ffd54f; outline-offset:2px;}
</style>''', unsafe_allow_html=True)

def balls_html(nums, special=None):
    parts = []
    for n in nums:
        extra = " special" if special is not None and int(n) == int(special) else ""
        parts.append(f'<span class="ball {BALL_COLOR[int(n)]}{extra}">{int(n):02d}</span>')
    return "".join(parts)

st.title("Mark Six R&D Lab")
st.caption("多策略實驗台。預設用第5代攪珠機（2026-05-05 起）。")

all_draws = load_processed()
if not all_draws:
    st.warning("尚無數據。")
    st.stop()

era = st.sidebar.selectbox("數據時期", options=list(ERAS.keys()), format_func=lambda k: ERAS[k], index=0)
draws, used = pick_working_set(all_draws, era=era, min_draws=12)
if used == "all_fallback":
    st.warning(f"第5代窗口（{GEN5_START} 起）期數不足，暫時用全部歷史。")
st.sidebar.caption(f"{len(draws)}/{len(all_draws)} draws · split {GEN5_START}")

s = summary(draws)
k1, k2, k3, k4 = st.columns(4)
k1.metric("歷史期數", s["n_draws"])
k2.metric("最近期號", (s["latest"] or {}).get("issue") or "—")
k3.metric("最近日期", (s["latest"] or {}).get("date") or "—")
k4.metric("策略數", len(STRATEGIES))
chi = s.get("chi2_uniform") or {}
st.caption(f"均匀 χ² = {chi.get('chi2', 0):.1f} (df=48)")

if s["latest"]:
    latest = draws[-1]
    st.markdown("**最近開獎** " + balls_html(latest.mains) + " + " + balls_html([latest.special], latest.special), unsafe_allow_html=True)

seed = st.sidebar.number_input("策略隨機種子", min_value=1, max_value=99999, value=42)

st.header("各策略預測")
for t in all_tickets(draws, seed=int(seed)):
    c1, c2 = st.columns((3, 2))
    with c1:
        st.subheader(t["name"])
        st.markdown(balls_html(t["mains"]) + " &nbsp;特 " + balls_html([t["special"]], t["special"]), unsafe_allow_html=True)
    with c2:
        st.caption(t.get("note", ""))
        st.write(f"單數 {t['odd']}　大號 {t['high']}")

st.header("頻率")
freq = frequency(draws)
df = pd.DataFrame({"number": list(freq.keys()), "count": list(freq.values())}).sort_values("number")
df["color"] = df["number"].map(BALL_COLOR)
st.plotly_chart(px.bar(df, x="number", y="count", color="color",
    color_discrete_map={"red": "#d32f2f", "blue": "#1565c0", "green": "#2e7d32"}), use_container_width=True)

st.header("Walk-forward")
bt = compare_all(draws, min_history=max(10, min(20, max(len(draws)//3, 8))))
btdf = pd.DataFrame(bt)
st.dataframe(btdf, use_container_width=True)
fig2 = px.bar(btdf, x="strategy", y="mean_mains_hit")
fig2.add_hline(y=6 * 6 / 49, line_dash="dash")
st.plotly_chart(fig2, use_container_width=True)
