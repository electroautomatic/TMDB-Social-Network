# Настройка автоматического деплоя на VDS через GitHub Actions

Данный документ описывает шаги по настройке автоматического деплоя Django проекта на VDS сервер с использованием GitHub Actions.

## Предварительные требования

- VDS сервер с установленными Docker и docker-compose
- Репозиторий проекта на GitHub
- SSH доступ к VDS серверу
- Доменное имя (опционально)

## Шаг 1: Настройка VDS сервера

1. Установите Git, Docker и docker-compose на ваш VDS сервер.

```bash
# Установка Git
sudo apt update
sudo apt install git

# Установка Docker
sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt update
sudo apt install docker-ce

# Установка docker-compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.15.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. Клонируйте репозиторий проекта на сервер:

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

3. Настройте переменные окружения для продакшена:

```bash
cp .env.production.example .env.production
nano .env.production  # Отредактируйте переменные под ваши нужды
```

4. Запустите проект вручную, чтобы убедиться, что всё работает:

```bash
docker-compose up -d
```

5. Настройте автоматическое обновление из репозитория:

```bash
chmod +x deploy.sh
```

## Шаг 2: Настройка SSH ключей для GitHub Actions

1. Создайте пару SSH ключей (без пароля) на вашем локальном компьютере:

```bash
ssh-keygen -t ed25519 -C "github-actions" -f github-actions
```

2. Добавьте публичный ключ на ваш VDS сервер:

```bash
# На локальном компьютере
cat github-actions.pub
```

Скопируйте вывод и добавьте его в файл `~/.ssh/authorized_keys` на VDS сервере.

3. Проверьте подключение:

```bash
ssh -i github-actions username@your-server-ip
```

## Шаг 3: Настройка GitHub Secrets

В вашем GitHub репозитории перейдите в Settings > Secrets and variables > Actions и добавьте следующие секреты:

- `SSH_PRIVATE_KEY`: содержимое приватного ключа (файл `github-actions` без расширения)
- `HOST`: IP-адрес вашего VDS сервера
- `USERNAME`: имя пользователя на сервере
- `PORT`: SSH порт (обычно 22)
- `DEPLOY_PATH`: путь к директории проекта на сервере (например, `/home/username/your-repo`)
- `TMDB_API_KEY`: ваш ключ API от TMDB

## Шаг 4: Настройка GitHub Actions Workflow

Файл `.github/workflows/deploy.yml` уже создан в репозитории. При каждом пуше в ветку `main`, GitHub Actions будет автоматически деплоить ваше приложение на VDS.

## Шаг 5: Первый деплой

1. Сделайте коммит и пуш в ветку `main`:

```bash
git add .
git commit -m "Setup CI/CD deployment"
git push origin main
```

2. Перейдите в раздел Actions вашего GitHub репозитория, чтобы отслеживать процесс деплоя.

## Дополнительные настройки

### Настройка Nginx (опционально)

Если вы хотите использовать доменное имя и HTTPS, вам потребуется настроить Nginx в качестве обратного прокси-сервера.

1. Установите Nginx:

```bash
sudo apt install nginx
```

2. Создайте конфигурацию для вашего сайта:

```bash
sudo nano /etc/nginx/sites-available/your-domain.conf
```

3. Добавьте следующую конфигурацию:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/your/repo/static/;
        expires 30d;
    }

    location /media/ {
        alias /path/to/your/repo/media/;
        expires 30d;
    }
}
```

4. Активируйте конфигурацию:

```bash
sudo ln -s /etc/nginx/sites-available/your-domain.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Настройка HTTPS с Let's Encrypt (опционально)

1. Установите Certbot:

```bash
sudo apt install certbot python3-certbot-nginx
```

2. Получите сертификат:

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

3. Настройте автоматическое обновление сертификатов:

```bash
sudo systemctl status certbot.timer
```

## Устранение неполадок

Если возникают проблемы с деплоем, проверьте:

1. Логи GitHub Actions в разделе Actions вашего репозитория
2. Логи контейнеров на сервере: `docker-compose logs`
3. Права доступа к файлам и директориям проекта
4. Правильность указанных секретов в GitHub

## Дополнительные ресурсы

- [GitHub Actions документация](https://docs.github.com/en/actions)
- [Docker документация](https://docs.docker.com/)
- [Django деплой с Docker](https://docs.djangoproject.com/en/5.1/howto/deployment/) 