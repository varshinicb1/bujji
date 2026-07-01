FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
RUN uv sync --no-dev

COPY . .
RUN uv build

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/dist/*.whl /tmp/
RUN pip install /tmp/*.whl && rm /tmp/*.whl

RUN mkdir -p /root/.bujji

COPY bujji.yaml /root/.bujji/

EXPOSE 8000

CMD ["uvicorn", "bujji.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
