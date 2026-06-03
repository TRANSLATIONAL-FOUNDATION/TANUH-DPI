FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/tmp/hf_cache \
    HUGGINGFACE_HUB_CACHE=/tmp/hf_cache

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    libglib2.0-0 \
    libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY privacy_filter/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common/ ./common/
COPY privacy_filter/__init__.py ./privacy_filter/__init__.py
COPY privacy_filter/app/ ./app/

ENV LOCAL_DATA_DIR=/tmp/data
ENV PYTHONPATH=/app
RUN mkdir -p /tmp/data/uploads /tmp/data/redacted /tmp/hf_cache

EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003", "--workers", "1"]
