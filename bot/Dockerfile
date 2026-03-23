ARG REGISTRY_PREFIX=harbor.pg.innopolis.university/docker-hub-cache/
FROM ${REGISTRY_PREFIX}python:3.11-slim

WORKDIR /app

# Устанавливаем uv (не pip install зависимостей проекта — только сам uv)
RUN pip install uv

# Копируем только файлы зависимостей — слой кешируется отдельно
COPY bot/pyproject.toml bot/uv.lock ./

# Устанавливаем зависимости через uv sync (как требует задание)
RUN uv sync --frozen --no-dev

# Копируем весь код бота
COPY bot/ .

CMD ["uv", "run", "python", "bot.py"]
