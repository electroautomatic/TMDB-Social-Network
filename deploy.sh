#!/bin/bash

# Скрипт для деплоя приложения на VDS
# Должен располагаться в корневой директории проекта на сервере

set -e  # Остановка выполнения при ошибке

echo "Starting deployment..."

# 1. Обновление кода из репозитория
echo "Pulling latest changes from Git..."
git pull

# 2. Обновление переменных окружения (опционально)
if [ -f ".env.production" ]; then
    echo "Updating environment variables..."
    cp .env.production .env
fi

# 3. Остановка и пересборка Docker контейнеров
echo "Rebuilding and restarting Docker containers..."
docker-compose down
docker-compose build
docker-compose up -d

# 4. Применение миграций Django (внутри контейнера)
echo "Running database migrations..."
docker-compose exec -T web python manage.py migrate

# 5. Сбор статических файлов (опционально)
echo "Collecting static files..."
docker-compose exec -T web python manage.py collectstatic --noinput

# 6. Очистка неиспользуемых Docker образов (опционально)
echo "Cleaning up unused Docker images..."
docker image prune -f

echo "Deployment completed successfully!" 