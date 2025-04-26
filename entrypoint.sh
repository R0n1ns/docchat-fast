#!/bin/bash

# Функция для ожидания доступности PostgreSQL
postgres_ready() {
    python << END
import sys
import psycopg2
import os

try:
    dbname = os.environ.get("PGDATABASE", "postgres")
    user = os.environ.get("PGUSER", "postgres")
    password = os.environ.get("PGPASSWORD", "postgres")
    host = os.environ.get("PGHOST", "localhost")
    port = os.environ.get("PGPORT", "5432")
    
    conn = psycopg2.connect(
        dbname=dbname, 
        user=user, 
        password=password, 
        host=host, 
        port=port
    )
except psycopg2.OperationalError:
    sys.exit(1)
sys.exit(0)
END
}

echo "Waiting for PostgreSQL..."

# Ожидание доступности базы данных
until postgres_ready; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

>&2 echo "PostgreSQL is available - continuing..."

# Инициализация базы данных с созданием админа
echo "Initializing database..."
python init_db.py

# Создание директории для загрузок, если она не существует
mkdir -p uploads

# Выполнение переданной команды (или запуск по умолчанию)
exec "$@"