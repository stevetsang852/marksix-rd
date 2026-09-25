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
from marksix_rd.strategies import all_tickets

st.set_page_config(page_title="Mark Six R&D Lab", layout="wide")
st.title("Mark Six R&D Lab")
st.caption("數據分析／機械學習研究用。攪珠為隨機事件，策略不能改變負期望值。")

draws = load_processed()
if not draws:
    st.warning("尚無 processed 數據。")
    st.stop()

s = summary(draws)
c1, c2, c3 = st.columns(3)
c1.metric("歷史期數", s["n_draws"])
if s["latest"]:
    c2.metric("最近期號", s["latest"]["issue"] or "—")
    c3.metric("最近日期", s["latest"]["date"] or "—")

left, right = st.columns((2, 1))
with left:
    freq = frequency(draws)
    df = pd.DataFrame({"number": list(freq.keys()), "count": list(freq.values())}).sort_values("number")
    fig = px.bar(df, x="number", y="count", title="號碼出現次數（含特別號碼）")
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("熱號")
    st.table(pd.DataFrame(s["hot"], columns=["號碼", "次數"]))
    st.subheader("冷號（間隔）")
    st.table(pd.DataFrame(s["cold_by_gap"], columns=["號碼", "未出現期數"]))

st.subheader("研究候選組合（非投注建議）")
st.dataframe(pd.DataFrame(all_tickets(draws)), use_container_width=True)
st.subheader("Walk-forward 回測 vs 隨機期望")
st.dataframe(pd.DataFrame(compare_all(draws)), use_container_width=True)
st.info("隨機基準：每期 6 個正碼期望命中 ≈ 0.735；特別號命中率 ≈ 2.04%。")
st.subheader("最近開獎")
st.dataframe(pd.DataFrame([d.to_dict() for d in draws[-20:]]), use_container_width=True)
