# marksix-rd

香港六合彩 **數據分析／機械學習研究實驗室**（不是投注系統、不是必中工具）。

Repo: https://github.com/stevetsang852/marksix-rd

攪珠是隨機事件，長期期望值為負。本專案把「策略能不能打敗均匀隨機」當成要檢驗的假說，用 walk-forward 回測與官方波色／機代分窗來驗證。

## 快速開始

### Docker（建議）

```bash
docker compose up --build dashboard
```

瀏覽器：http://localhost:8501

```bash
docker compose --profile test run --rm test
docker compose --profile api up api
```

### 本機 Python

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
pytest -q
streamlit run app/dashboard.py
uvicorn app.api:app --reload --app-dir .
```

沒有 `data/processed/draws.json` 時會讀 `data/sample_draws.csv`（示範列，非正式完整歷史）。
匯入完整可重現資料時，系統會優先使用 `data/processed/draws.json`，再用 bundled CSV 補缺口。

## Dashboard

頂部分頁依攪珠機代排列，**第5代是主力**：

| 分頁 | 服役（公開報導） | 用途 |
|---|---|---|
| 第5代 | 2026-05-05 起（26/047） | 策略研究單 + 回測 |
| 第4代 | 2010-11-09 – 2026-05-02 | 對照統計 |
| 第3代 | 1995 – 2010-11-08 | 對照統計 |
| 全部 | — | 對照，不當下期模型 |

目前已匯入的可重現歷史 CSV 覆蓋 **2002-07-04 起**，所以第3代有 2002–2010 的資料。第1–2代在 dashboard 隱藏，待有可靠 pre-2002 原始資料來源後可再顯示。

## 數據更新

```bash
python -m marksix_rd.ingest
```

Ingest 會嘗試讀官方最近 30 期，並支援 2002 至今的歷史 CSV raw snapshot。若 Docker／CI 網絡不能連外，只要 `data/raw/hkjc_history_2002_now*.csv` 已存在，仍會用本地 raw snapshot 重建 `data/processed/draws.json`。

## 策略

`random` `hot` `cold` `balanced` `color_spread` `sum_band` `pair_affinity` `exp_smooth` `sklearn_rank` `ensemble`

回測基準：正碼期望命中 ≈ `6×6/49 ≈ 0.735`；特別號 ≈ `1/49 ≈ 2.04%`。波色用馬會官方紅／藍／綠。

## 結構

```
src/marksix_rd/
app/dashboard.py
app/api.py
data/
Dockerfile
docker-compose.yml
.github/workflows/ci.yml
.github/workflows/ingest-hkjc.yml
```

## CI

- **test** — Python 3.12 + pytest
- **docker** — build 後在映像內再跑 pytest
- **ingest-hkjc-daily** — 15:05 UTC 抓 `last30draw.json` 到 `data/raw/`

Private repo 請先在 Actions 啟用 workflows。

## 邊界

換機只是制度分窗，不等於新機可預測。馬會開獎數據版權屬香港馬會；本 repo 僅供個人研究。
