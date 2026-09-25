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
from marksix_rd.era import ERAS, GENS, TAB_ORDER, filter_era
from marksix_rd.ingest import load_processed
from marksix_rd.schema import BALL_COLOR
from marksix_rd.strategies import all_tickets

st.set_page_config(page_title="Mark Six R&D Lab", layout="wide")
st.markdown('<style>.ball{display:inline-flex;align-items:center;justify-content:center;width:40px;height:40px;border-radius:50%;margin:0 3px;color:#fff;font-weight:700}.ball.red{background:#d32f2f}.ball.blue{background:#1565c0}.ball.green{background:#2e7d32}.ball.special{outline:3px solid #ffd54f;outline-offset:2px}</style>', unsafe_allow_html=True)

def balls_html(nums, special=None):
    parts=[]
    for n in nums:
        extra=" special" if special is not None and int(n)==int(special) else ""
        parts.append(f'<span class="ball {BALL_COLOR[int(n)]}{extra}">{int(n):02d}</span>')
    return "".join(parts)

def render_panel(draws, seed, title, blurb, primary):
    if primary:
        st.success("主力分析窗口：第5代攪珠機。策略與回測都只用這頁數據。")
    st.caption(blurb)
    if not draws:
        st.warning("這個機代目前沒有已匯入的開獎。")
        return
    s = summary(draws)
    a,b,c,d = st.columns(4)
    a.metric("期數", s["n_draws"])
    b.metric("最近期號", (s["latest"] or {}).get("issue") or "—")
    c.metric("最近日期", (s["latest"] or {}).get("date") or "—")
    d.metric("χ²", f"{(s.get('chi2_uniform') or {}).get('chi2',0):.1f}")
    if s["latest"]:
        last = draws[-1]
        st.markdown("**最近開獎** "+balls_html(last.mains)+" + "+balls_html([last.special], last.special), unsafe_allow_html=True)
    st.subheader("策略研究單")
    if primary:
        for t in all_tickets(draws, seed=seed):
            left, right = st.columns((3,2))
            with left:
                st.markdown(f"**{t['name']}**")
                st.markdown(balls_html(t["mains"])+" 特 "+balls_html([t["special"]], t["special"]), unsafe_allow_html=True)
            with right:
                st.caption(t.get("note",""))
    else:
        st.info("舊機分頁只做對照統計。")
    freq = frequency(draws)
    df = pd.DataFrame({"number": list(freq.keys()), "count": list(freq.values())}).sort_values("number")
    df["color"] = df["number"].map(BALL_COLOR)
    st.plotly_chart(px.bar(df, x="number", y="count", color="color", color_discrete_map={"red":"#d32f2f","blue":"#1565c0","green":"#2e7d32"}, title=f"{title} 頻率"), use_container_width=True)
    if primary and len(draws) >= 16:
        bt = pd.DataFrame(compare_all(draws, min_history=max(8, min(16, len(draws)//3))))
        fig = px.bar(bt, x="strategy", y="mean_mains_hit")
        fig.add_hline(y=6*6/49, line_dash="dash")
        st.plotly_chart(fig, use_container_width=True)

st.title("Mark Six R&D Lab")
st.caption("分頁 = 攪珠機代。預測主力在第5代。")
all_draws = load_processed()
if not all_draws:
    st.warning("尚無數據。")
    st.stop()
seed = st.sidebar.number_input("策略隨機種子", min_value=1, max_value=99999, value=42)
for key in TAB_ORDER:
    n = len(all_draws) if key=="all" else len(filter_era(all_draws, key))
    st.sidebar.write(f"{ERAS[key]}: {n}")
tabs = st.tabs([ERAS[k] for k in TAB_ORDER])
for tab, key in zip(tabs, TAB_ORDER):
    with tab:
        if key == "all":
            render_panel(all_draws, int(seed), "全部", "對照用", False)
        else:
            meta = GENS[key]
            render_panel(filter_era(all_draws, key), int(seed), meta["label"], meta["blurb"], bool(meta["primary"]))
