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
from marksix_rd.era import DISPLAY_TAB_ORDER, ERAS, GENS, filter_era
from marksix_rd.ingest import load_processed
from marksix_rd.schema import BALL_COLOR
from marksix_rd.strategies import STRATEGY_DETAILS, all_tickets

st.set_page_config(page_title="Mark Six R&D Lab", layout="wide")
st.markdown('<style>.ball{display:inline-flex;align-items:center;justify-content:center;width:38px;height:38px;border-radius:50%;margin:0 3px;color:#fff;font-weight:700}.ball.red{background:#d32f2f}.ball.blue{background:#1565c0}.ball.green{background:#2e7d32}.ball.special{outline:3px solid #ffd54f;outline-offset:2px}.pred-card{border:1px solid #3333;border-radius:12px;padding:10px 12px;margin-bottom:8px}</style>', unsafe_allow_html=True)

DEFAULT_SEED = 42
MIN_SEED = 1
MAX_SEED = 99999

def balls_html(nums, special=None):
    parts=[]
    for n in nums:
        extra=" special" if special is not None and int(n)==int(special) else ""
        parts.append(f'<span class="ball {BALL_COLOR[int(n)]}{extra}">{int(n):02d}</span>')
    return "".join(parts)

def query_seed():
    raw = st.query_params.get("seed")
    if isinstance(raw, list):
        raw = raw[0] if raw else None
    if raw in (None, ""):
        return DEFAULT_SEED
    try:
        seed = int(raw)
    except ValueError:
        st.sidebar.warning(f"URL seed={raw!r} 不是有效整數，已改用 {DEFAULT_SEED}。")
        return DEFAULT_SEED
    if MIN_SEED <= seed <= MAX_SEED:
        return seed
    st.sidebar.warning(f"URL seed 必須介乎 {MIN_SEED} 至 {MAX_SEED}，已改用 {DEFAULT_SEED}。")
    return DEFAULT_SEED

def render_strategy_help():
    with st.expander("策略點樣睇？（按此查看詳細解釋）", expanded=True):
        st.markdown(
            """
            **重點：**以下全部是研究策略，不是投注建議，也不是必中工具。

            「策略隨機種子」只控制策略內的隨機抽樣；同一個 seed + 同一批資料會產生同一張研究單，方便你 refresh 後重現結果。
            """
        )
        rows = [
            {
                "策略": detail["label"],
                "點揀號碼": detail["summary"],
                "用來研究": detail["use"],
                "注意": detail["watch"],
            }
            for detail in STRATEGY_DETAILS.values()
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

def render_predictions(draws, seed):
    st.header("各策略預測（下一期研究單）")
    st.caption("用第5代窗口計算。研究候選，不是投注建議。")
    render_strategy_help()
    tickets = all_tickets(draws, seed=seed)
    rows=[]
    for t in tickets:
        detail = STRATEGY_DETAILS.get(t["name"], {})
        title = detail.get("label", t["name"])
        st.markdown(f'<div class="pred-card"><b>{title}</b> <span style="opacity:.65">({t["name"]})</span>　{balls_html(t["mains"])}　特 {balls_html([t["special"]], t["special"])}<br><span style="opacity:.75">{t.get("note","")}　單數 {t["odd"]}　大號 {t["high"]}</span></div>', unsafe_allow_html=True)
        rows.append({"strategy":t["name"],"name":title,"n1":t["mains"][0],"n2":t["mains"][1],"n3":t["mains"][2],"n4":t["mains"][3],"n5":t["mains"][4],"n6":t["mains"][5],"special":t["special"],"odd":t["odd"],"high":t["high"],"note":t.get("note","")})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

def render_panel(draws, title, blurb):
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
    freq = frequency(draws)
    df = pd.DataFrame({"number": list(freq.keys()), "count": list(freq.values())}).sort_values("number")
    df["color"] = df["number"].map(BALL_COLOR)
    st.plotly_chart(px.bar(df, x="number", y="count", color="color", color_discrete_map={"red":"#d32f2f","blue":"#1565c0","green":"#2e7d32"}, title=f"{title} 頻率"), use_container_width=True)

st.title("Mark Six R&D Lab")
st.caption("預測板永遠在最上面；下方分頁是各代統計。")
all_draws = load_processed()
if not all_draws:
    st.warning("尚無數據。"); st.stop()
seed = st.sidebar.number_input("策略隨機種子", min_value=MIN_SEED, max_value=MAX_SEED, value=query_seed(), key="strategy_seed")
if st.query_params.get("seed") != str(int(seed)):
    st.query_params["seed"] = str(int(seed))
st.sidebar.caption("Seed 會寫入 URL，所以 refresh 後會保留同一組策略結果。")
for key in DISPLAY_TAB_ORDER:
    n = len(all_draws) if key=="all" else len(filter_era(all_draws, key))
    st.sidebar.write(f"{ERAS[key]}：{n}")
gen5 = filter_era(all_draws, "gen5")
pred_draws = gen5 if len(gen5)>=8 else all_draws
if pred_draws:
    last = pred_draws[-1]
    st.markdown(f"預測窗口最近 **{last.issue}** {last.date} "+balls_html(last.mains)+" + "+balls_html([last.special], last.special), unsafe_allow_html=True)
render_predictions(pred_draws, int(seed))
st.divider(); st.subheader("Walk-forward 回測")
if len(pred_draws)>=16:
    bt = pd.DataFrame(compare_all(pred_draws, min_history=max(8, min(16, len(pred_draws)//3))))
    fig = px.bar(bt, x="strategy", y="mean_mains_hit")
    fig.add_hline(y=6*6/49, line_dash="dash")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(bt, use_container_width=True)
st.divider(); st.subheader("機代對照")
tabs = st.tabs([ERAS[k] for k in DISPLAY_TAB_ORDER])
for tab, key in zip(tabs, DISPLAY_TAB_ORDER):
    with tab:
        if key=="all":
            render_panel(all_draws, "全部", "對照用。")
        else:
            meta=GENS[key]
            render_panel(filter_era(all_draws, key), meta["label"], meta["blurb"])
