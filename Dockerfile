# Dockerfile for Streamlit + uv + DuckDB app

FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency metadata first for caching
COPY pyproject.toml uv.lock ./

RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv sync --no-editable

# Now copy the rest of the project
COPY . .

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

EXPOSE 8501

CMD ["streamlit", "run", "app/main.py"]
