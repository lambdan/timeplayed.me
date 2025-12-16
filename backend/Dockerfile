#FROM python:3.13.1-slim
FROM python:3.13-slim

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
  curl  \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN python -m venv .venv && \
  .venv/bin/pip install --upgrade pip && \
  .venv/bin/pip install -r requirements.txt

COPY tpbackend /app/tpbackend

# Check formatting has been applied
RUN python -m venv .venv && .venv/bin/python -m black --check /app/tpbackend

ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "-m", "tpbackend.main"]
