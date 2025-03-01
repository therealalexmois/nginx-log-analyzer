FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml poetry.lock ./
COPY src ./src

RUN pip install --upgrade pip \
    && pip install "poetry==2.0.1" \
    && poetry install --no-root --without dev,test

ENTRYPOINT ["poetry", "run", "python", "-m", "src.nginx_log_analyzer.main"]

CMD ["--config", "/config/config.toml"]
