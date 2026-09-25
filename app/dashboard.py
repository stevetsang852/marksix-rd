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
st.caption("多策略數據實驗台。攪珠為隨機；以下是研究候選，不是投注建議。")

draws = load_processed()
if not draws:
    st.warning("尚無數據。")
    st.stop()

s = summary(draws)
k1, k2, k3, k4 = st.columns(4)
k1.metric("歷史期數", s["n_draws"])
k2.metric("最近期號", (s["latest"] or {}).get("issue") or "—")
k3.metric("最近日期", (s["latest"] or {}).get("date") or "—")
k4.metric("策略數", len(STRATEGIES))

if s["latest"]:
    latest = draws[-1]
    st.markdown("**最近開獎** " + balls_html(latest.mains) + " + " + balls_html([latest.special], latest.special), unsafe_allow_html=True)

seed = st.sidebar.number_input("策略隨機種子", min_value=1, max_value=99999, value=42)

st.header("各策略預測（下一期研究單）")
for t in all_tickets(draws, seed=int(seed)):
    c1, c2 = st.columns((3, 2))
    with c1:
        st.subheader(t["name"])
        st.markdown(balls_html(t["mains"]) + " &nbsp;特 " + balls_html([t["special"]], t["special"]), unsafe_allow_html=True)
    with c2:
        st.caption(t.get("note", ""))
        st.write(f"單數 {t['odd']}　大號(≥25) {t['high']}")

st.header("頻率")
freq = frequency(draws)
df = pd.DataFrame({"number": list(freq.keys()), "count": list(freq.values())}).sort_values("number")
df["color"] = df["number"].map(BALL_COLOR)
st.plotly_chart(px.bar(df, x="number", y="count", color="color",
    color_discrete_map={"red": "#d32f2f", "blue": "#1565c0", "green": "#2e7d32"},
    title="號碼出現次數（含特別號）"), use_container_width=True)

h, c = st.columns(2)
with h:
    st.subheader("熱號")
    st.table(pd.DataFrame(s["hot"], columns=["號碼", "次數"]))
with c:
    st.subheader("冷號（間隔）")
    st.table(pd.DataFrame(s["cold_by_gap"], columns=["號碼", "未出現期數"]))

st.header("Walk-forward 回測")
bt = compare_all(draws, min_history=max(10, min(20, len(draws) // 3)))
btdf = pd.DataFrame(bt)
st.dataframe(btdf, use_container_width=True)
fig2 = px.bar(btdf, x="strategy", y="mean_mains_hit", title="平均正碼命中（隨機期望 ≈ 0.735）")
fig2.add_hline(y=6 * 6 / 49, line_dash="dash", annotation_text="random E")
st.plotly_chart(fig2, use_container_width=True)
st.info("若策略不能穩定高於虛線，視為無預測力。")
st.header("最近開獎表")
st.dataframe(pd.DataFrame([d.to_dict() for d in draws[-25:]]), use_container_width=True)
