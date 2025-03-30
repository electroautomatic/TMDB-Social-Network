#!/bin/bash

# Скрипт для запуска проекта в режиме разработки

# Цветовые коды для вывода
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}Запуск TMDB Social в режиме разработки...${NC}"

# Остановка существующих контейнеров
echo -e "${GREEN}Остановка существующих контейнеров...${NC}"
docker-compose down

# Запуск с конфигурацией для разработки
echo -e "${GREEN}Запуск контейнеров с конфигурацией для разработки...${NC}"
docker-compose up -d

# Применение миграций (если нужно)
echo -e "${GREEN}Применение миграций базы данных...${NC}"
docker-compose exec web python manage.py migrate

echo -e "${GREEN}Проект запущен в режиме разработки!${NC}"
echo -e "${GREEN}Доступен по адресу: http://localhost:8000${NC}" 