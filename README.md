# marksix-rd

香港六合彩 **數據分析／機械學習研究實驗室**（非投注系統）。

Repo: https://github.com/stevetsang852/marksix-rd

詳見源碼 README 內結構、參考專案與 Actions 說明。

本機：

```bash
pip install -r requirements.txt
export PYTHONPATH=src
pytest -q
streamlit run app/dashboard.py
```

Daily CI cron 15:05 UTC fetches `https://bet.hkjc.com/contentserver/jcbw/cmc/last30draw.json` into `data/raw/`.
