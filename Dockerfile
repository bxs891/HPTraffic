FROM python:3.11-slim

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml README.md /code/
COPY app /code/app
COPY migrations /code/migrations
COPY alembic.ini /code/alembic.ini

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .[dev]

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
