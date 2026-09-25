FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY src ./src
COPY app ./app
COPY data ./data
COPY tests ./tests

EXPOSE 8501 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app/dashboard.py", "--server.address=0.0.0.0", "--server.port=8501"]
