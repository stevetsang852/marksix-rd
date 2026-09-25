"""Research ticket generators. Not betting advice."""
from __future__ import annotations
import random
from collections import Counter
from typing import Callable
import numpy as np
from .features import number_features
from .schema import BALL_COLOR, Draw

def _finish(name, mains, special, note=""):
    mains = sorted(int(x) for x in mains)
    special = int(special)
    if special in mains:
        special = next(n for n in range(1, 50) if n not in mains)
    return {"name": name, "mains": mains, "special": special, "note": note, "colors": [BALL_COLOR[n] for n in mains], "odd": sum(n % 2 for n in mains), "high": sum(1 for n in mains if n >= 25)}

def _weighted_sample(weights, k, rng):
    pool = list(range(1, 50))
    pool_w = [max(float(weights.get(n, 0.0)), 1e-9) for n in pool]
    picked = []
    for _ in range(k):
        total = sum(pool_w)
        r = rng.random() * total
        acc = 0.0
        idx = 0
        for i, ww in enumerate(pool_w):
            acc += ww
            if acc >= r:
                idx = i
                break
        picked.append(pool[idx])
        pool.pop(idx); pool_w.pop(idx)
    return picked

def strategy_random(draws, seed=42):
    rng = random.Random(seed)
    mains = sorted(rng.sample(range(1, 50), 6))
    special = rng.choice([n for n in range(1, 50) if n not in mains])
    return _finish("random", mains, special, "uniform baseline")

def strategy_hot(draws, seed=42):
    from collections import Counter
    c = Counter()
    for d in draws:
        c.update(d.mains)
    mains = [n for n,_ in c.most_common(6)] or list(range(1,7))
    special = next((n for n,_ in c.most_common() if n not in mains), 1)
    return _finish("hot", mains, special, "highest historical frequency")

def strategy_cold(draws, seed=42):
    last = {n: -1 for n in range(1,50)}
    for i,d in enumerate(draws):
        for n in d.mains:
            last[n]=i
    ranked = sorted(range(1,50), key=lambda n: last[n])
    mains = ranked[:6]
    special = next(n for n in ranked[6:] if n not in mains)
    return _finish("cold", mains, special, "longest absence (overdue)")

def strategy_balanced(draws, seed=42):
    h=strategy_hot(draws, seed); c=strategy_cold(draws, seed)
    mains=sorted(list(dict.fromkeys(h["mains"][:3]+c["mains"][:3])))[:6]
    while len(mains)<6:
        n=next(x for x in range(1,50) if x not in mains); mains.append(n)
    special=h["special"] if h["special"] not in mains else c["special"]
    return _finish("balanced", mains, special, "mix hot + cold pool")

def strategy_color_spread(draws, seed=42):
    from collections import defaultdict
    buckets=defaultdict(list)
    for n in range(1,50):
        buckets[BALL_COLOR[n]].append(n)
    rng=random.Random(seed+3)
    mains=[]
    for col in ("red","blue","green"):
        mains.extend(rng.sample(buckets[col], 2))
    special=rng.choice([n for n in range(1,50) if n not in mains])
    return _finish("color_spread", mains, special, "2 red + 2 blue + 2 green")

def strategy_sum_band(draws, seed=42):
    rng=random.Random(seed+5)
    target=135
    best=None; best_d=10**9
    for _ in range(400):
        m=sorted(rng.sample(range(1,50),6))
        d=abs(sum(m)-target)
        if d<best_d:
            best, best_d=m,d
    special=rng.choice([n for n in range(1,50) if n not in best])
    return _finish("sum_band", best, special, "target sum ≈ 135")

def strategy_pair_affinity(draws, seed=42):
    pairs=Counter()
    for d in draws:
        m=list(d.mains)
        for i in range(len(m)):
            for j in range(i+1,len(m)):
                pairs[(m[i],m[j])]+=1
    if not pairs:
        return strategy_hot(draws, seed)
    a,b=max(pairs, key=pairs.get)
    chosen=[a,b]
    while len(chosen)<6:
        scores=Counter()
        for (x,y),c in pairs.items():
            if x in chosen and y not in chosen: scores[y]+=c
            if y in chosen and x not in chosen: scores[x]+=c
        nxt=scores.most_common(1)[0][0] if scores else next(n for n in range(1,50) if n not in chosen)
        chosen.append(nxt)
    special=next(n for n in range(1,50) if n not in chosen)
    return _finish("pair_affinity", chosen, special, "grow from most common pair")

def strategy_exp_smooth(draws, seed=42):
    feats=number_features(draws); rec=feats[:,2]
    w={n:float(rec[n-1]) for n in range(1,50)}
    rng=random.Random(seed)
    mains=sorted(_weighted_sample(w,6,rng))
    special=max((n for n in range(1,50) if n not in mains), key=lambda n:w[n])
    return _finish("exp_smooth", mains, special, "exponential recency weights")

def strategy_sklearn_rank(draws, seed=42):
    if len(draws)<16:
        t=strategy_hot(draws, seed); t["name"]="sklearn_rank"; t["note"]="fallback hot"; return t
    xs=[]; ys=[]
    for t in range(8,len(draws)):
        xs.append(number_features(draws[:t]))
        lab=np.zeros(49)
        for n in draws[t].all_seven(): lab[n-1]=1.0
        ys.append(lab)
    Xtr=np.vstack(xs); ytr=np.concatenate(ys)
    try:
        from sklearn.linear_model import Ridge
        model=Ridge(alpha=2.0); model.fit(Xtr,ytr)
        scores=model.predict(number_features(draws)); note="Ridge rank on freq/gap/recency"
    except Exception:
        eye=np.eye(Xtr.shape[1])
        beta=np.linalg.pinv(Xtr.T@Xtr+2.0*eye)@Xtr.T@ytr
        scores=number_features(draws)@beta; note="numpy ridge rank"
    ranked=list(np.argsort(-scores)+1)
    mains=sorted(int(n) for n in ranked[:6])
    special=int(next(n for n in ranked[6:] if n not in mains))
    return _finish("sklearn_rank", mains, special, note)

def strategy_ensemble(draws, seed=42):
    votes=Counter(); specials=Counter()
    for fn in (strategy_hot, strategy_cold, strategy_balanced, strategy_exp_smooth, strategy_pair_affinity, strategy_sklearn_rank):
        t=fn(draws, seed); votes.update(t["mains"]); specials[t["special"]]+=1
    mains=[n for n,_ in votes.most_common(6)]
    special=next((n for n,_ in specials.most_common() if n not in mains),1)
    return _finish("ensemble", mains, special, "vote across 6 research strategies")

STRATEGIES={"random":strategy_random,"hot":strategy_hot,"cold":strategy_cold,"balanced":strategy_balanced,"color_spread":strategy_color_spread,"sum_band":strategy_sum_band,"pair_affinity":strategy_pair_affinity,"exp_smooth":strategy_exp_smooth,"sklearn_rank":strategy_sklearn_rank,"ensemble":strategy_ensemble}

STRATEGY_DETAILS = {
    "random": {
        "label": "Random 隨機基準",
        "summary": "完全平均隨機抽 6 個正碼，再抽 1 個特別號。",
        "use": "用來做基準線；其他策略至少要同它比較，否則沒有研究意義。",
        "watch": "不是模型，只是同一個 seed 會重複產生同一張隨機研究單。",
    },
    "hot": {
        "label": "Hot 熱號",
        "summary": "先數歷史正碼和特別號出現次數，再由最高頻的前 18 個號碼抽 6 個。",
        "use": "檢查近期／歷史高頻號碼是否有延續性。",
        "watch": "六合彩每期獨立隨機；熱號不代表下一期較大機會中。",
    },
    "cold": {
        "label": "Cold 冷號",
        "summary": "找出最久沒有出現的號碼，再由最長空窗的前 18 個號碼抽 6 個。",
        "use": "檢查「久未出現」是否有回補現象。",
        "watch": "久未出現不等於即將出現，這是常見賭徒謬誤風險。",
    },
    "balanced": {
        "label": "Balanced 冷熱混合",
        "summary": "把 hot 和 cold 的候選池合併，再抽 6 個正碼。",
        "use": "避免只追熱或只追冷，做較均衡的候選單。",
        "watch": "仍然依賴 hot/cold 的假設，不能當作提高中獎率的證明。",
    },
    "color_spread": {
        "label": "Color Spread 波色平均",
        "summary": "固定抽 2 紅、2 藍、2 綠，保持波色分佈平均。",
        "use": "研究波色分散的組合表現。",
        "watch": "波色是號碼分類，不是下一期結果的因果訊號。",
    },
    "sum_band": {
        "label": "Sum Band 總和帶",
        "summary": "參考歷史 6 個正碼總和的中位數，搜尋總和最接近的組合。",
        "use": "避免總和太極端，研究中間總和值區間。",
        "watch": "每個組合本身機率仍然一樣，總和貼近歷史不代表更準。",
    },
    "pair_affinity": {
        "label": "Pair Affinity 號碼配對",
        "summary": "由歷史最常同時出現的一對號碼開始，逐步加入與已選號碼同場次較多的號碼。",
        "use": "研究號碼兩兩共現關係。",
        "watch": "共現可能只是樣本巧合，尤其資料少時更不穩定。",
    },
    "exp_smooth": {
        "label": "Exp Smooth 近期權重",
        "summary": "近期開出的號碼權重較高，越舊的資料影響越低。",
        "use": "研究短期走勢或近期權重是否有訊號。",
        "watch": "近期權重高不代表有趨勢；隨機資料也會看似有走勢。",
    },
    "sklearn_rank": {
        "label": "Sklearn Rank 機器學習排序",
        "summary": "用頻率、空窗、近期權重等特徵訓練 Ridge 排序模型，選分數最高的號碼。",
        "use": "測試簡單 ML 特徵能否在 walk-forward 回測打敗隨機基準。",
        "watch": "資料太少會退回 hot；即使用 ML，也不代表可預測隨機攪珠。",
    },
    "ensemble": {
        "label": "Ensemble 集成投票",
        "summary": "集合 hot、cold、balanced、exp_smooth、pair_affinity、sklearn_rank 的選號投票。",
        "use": "降低單一策略偏差，觀察多策略共識。",
        "watch": "多個弱假設加起來不一定變強，仍需看回測。",
    },
}

def all_tickets(draws, seed=42):
    return [fn(draws, seed=seed) for fn in STRATEGIES.values()]

PLAIN_LOGIC={
    "random": "對照組。49 個號碼機會一樣，隨便抽 6+1。如果其他策略長期贏不了它，就沒有預測力。",
    "hot": "數過去每一顆球出現幾次，揣出現最多的 6 個。假設「常出的會再出」。",
    "cold": "看哪一顆最久沒開，揣欠開最長的。假設「欠得久就快輪到」。",
    "balanced": "一半熱號、一半冷號，避免全押同一種想法。",
    "color_spread": "馬會波是紅／藍／綠。刻意各揣 2 粒，讓顏色平均。",
    "sum_band": "六個正碼加起來通常落在中間一段。揣總和接近歷史中位的組合。",
    "pair_affinity": "先找最常一齊出現的一對號碼，再一顆一顆補上去。",
    "exp_smooth": "愈近的期愈重要。上期開過的權重大，十年前很小。",
    "sklearn_rank": "用每顆球的出現次數、隔了多久、近期熱度三個數字打分，取最高 6 個。",
    "ensemble": "六種策略各出一張單，哪顆被提名最多就入圍。多數決，不是魔法。",
}
