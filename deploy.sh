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

# Путь к проекту на сервере
PROJECT_DIR="/var/www/tmdb-project"

# Цветовые коды для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Начинаем деплой проекта TMDB Social...${NC}"

# Проверка наличия директорий и создание при необходимости
if [ ! -d "$PROJECT_DIR/media" ]; then
    echo -e "${GREEN}Создаем директорию для медиа-файлов...${NC}"
    mkdir -p "$PROJECT_DIR/media/posters/w500"
fi

if [ ! -d "$PROJECT_DIR/staticfiles" ]; then
    echo -e "${GREEN}Создаем директорию для статических файлов...${NC}"
    mkdir -p "$PROJECT_DIR/staticfiles"
fi

# Установка прав доступа
echo -e "${GREEN}Настройка прав доступа...${NC}"
sudo chown -R www-data:www-data "$PROJECT_DIR/media"
sudo chmod -R 755 "$PROJECT_DIR/media"
sudo chown -R www-data:www-data "$PROJECT_DIR/staticfiles"
sudo chmod -R 755 "$PROJECT_DIR/staticfiles"

# Настройка Nginx
echo -e "${GREEN}Настройка Nginx...${NC}"
sudo cp "$PROJECT_DIR/nginx/tmdb-project.conf" /etc/nginx/sites-available/tmdb-project
sudo ln -sf /etc/nginx/sites-available/tmdb-project /etc/nginx/sites-enabled/

# Проверка конфигурации Nginx
echo -e "${GREEN}Проверка конфигурации Nginx...${NC}"
sudo nginx -t
if [ $? -ne 0 ]; then
    echo -e "${RED}Ошибка в конфигурации Nginx! Деплой прерван.${NC}"
    exit 1
fi

# Перезапуск Nginx
echo -e "${GREEN}Перезапуск Nginx...${NC}"
sudo systemctl restart nginx

# Переход в директорию проекта
cd "$PROJECT_DIR"

# Остановка существующих контейнеров
echo -e "${GREEN}Остановка существующих контейнеров...${NC}"
docker-compose -f docker-compose.prod.yml down

# Сборка и запуск новых контейнеров
echo -e "${GREEN}Запуск контейнеров с продакшн-конфигурацией...${NC}"
docker-compose -f docker-compose.prod.yml up -d --build

# Сбор статических файлов
echo -e "${GREEN}Сбор статических файлов...${NC}"
docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# Применение миграций
echo -e "${GREEN}Применение миграций базы данных...${NC}"
docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate

echo -e "${GREEN}Деплой успешно завершен!${NC}"
echo -e "${GREEN}Проверьте работу сайта по адресу: http://103.90.75.250${NC}" 