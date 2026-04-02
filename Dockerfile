FROM python:3.12-slim

WORKDIR /app

# Устанавливаем системные зависимости (для psycopg2 и kafka)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Запускаем через gunicorn (как в продакшене)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]