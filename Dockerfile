FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt


FROM python:3.11-slim AS runtime

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# create non-root user
RUN addgroup --system sales \
    && adduser --system --ingroup sales sales

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080 \
    PATH="/opt/venv/bin:$PATH"

COPY --from=builder /opt/venv /opt/venv

COPY app app
COPY core core
COPY services services
COPY providers providers
COPY prompts prompts
COPY config config

# adjust permissions and switch to non-root user
RUN chown -R sales:sales /app
USER sales

EXPOSE ${PORT}
HEALTHCHECK CMD curl -fsS http://localhost:${PORT}/_stcore/health || exit 1
ENTRYPOINT ["sh", "-c", "streamlit run app/ui.py --server.port=${PORT} --server.address=0.0.0.0"]

