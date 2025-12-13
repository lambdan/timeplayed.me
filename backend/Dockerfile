#FROM python:3.13.1-slim
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt /app/
RUN python -m venv .venv && \
    .venv/bin/pip install --upgrade pip && \
    .venv/bin/pip install -r requirements.txt

COPY tpbackend /app/tpbackend

ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "-m", "tpbackend.main"]
