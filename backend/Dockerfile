FROM python:3.11-slim

# Устанавливаем Poetry
RUN pip install poetry

WORKDIR /app

# Копируем файлы с зависимостями
COPY pyproject.toml poetry.lock* ./

# Устанавливаем зависимости (без dev)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-dev

# Копируем код
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]