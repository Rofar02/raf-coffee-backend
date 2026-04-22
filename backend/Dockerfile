FROM python:3.12-slim

RUN pip install poetry

WORKDIR /app

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --without dev --no-root

RUN pip install --no-cache-dir python-multipart

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]