# Деплой `raf-coffee` на VPS Timeweb через Docker

Эта инструкция заточена под ваш текущий стек из `docker-compose.yml`:
- `postgres`
- `redis`
- `backend` (FastAPI)
- `frontend` (Nginx с проксированием API)

## 1) Подготовка VPS

Подключение:

```bash
ssh root@IP_СЕРВЕРА
```

Обновление системы:

```bash
apt update && apt upgrade -y
```

Создай отдельного пользователя:

```bash
adduser deploy
usermod -aG sudo deploy
```

Дальше работай из него:

```bash
su - deploy
```

---

## 2) Установка Docker и Compose plugin

```bash
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
docker --version
docker compose version
```

---

## 3) Клонирование проекта

```bash
git clone <URL_ТВОЕГО_РЕПО> raf-coffee
cd raf-coffee
```

---

## 4) Настройка переменных окружения

В вашем `docker-compose.yml` реально используется:
- `ADMIN_TOKEN` (для админ API)

Создай файл `.env` в корне проекта:

```bash
cd ~/raf-coffee
cat > .env << 'EOF'
ADMIN_TOKEN=СЛОЖНЫЙ_СЕКРЕТ_ЗАМЕНИ_МЕНЯ
EOF
```

`DATABASE_URL` и `REDIS_URL` уже заданы внутри compose для внутренних сервисов (`postgres`, `redis`).

---

## 5) Важно для продакшена: закрыть лишние порты БД и Redis

Сейчас compose публикует наружу:
- `5432:5432` (PostgreSQL)
- `6379:6379` (Redis)

Для продакшена это не нужно и небезопасно. Удали/закомментируй эти `ports` у `postgres` и `redis` в `docker-compose.yml`.

Оставь опубликованными только:
- `8080:80` у `frontend` (публичный вход)

Опционально:
- убрать `8000:8000` у `backend`, если API снаружи не нужен отдельно (через `frontend` он и так доступен по прокси).

---

## 6) Запуск проекта

```bash
cd ~/raf-coffee
docker compose up -d --build
docker compose ps
```

Проверки:

```bash
curl http://127.0.0.1:8080
curl http://127.0.0.1:8080/ping
```

---

## 7) Домен и SSL (Let's Encrypt)

### Вариант A (проще): SSL на хосте через Nginx

1. Установи Nginx и Certbot:

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

2. Настрой DNS: `A`-запись домена на IP VPS.

3. Конфиг Nginx (прокси на контейнер `frontend`, который слушает `127.0.0.1:8080`):

`/etc/nginx/sites-available/raf-coffee`

```nginx
server {
    listen 80;
    server_name your-domain.ru www.your-domain.ru;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

4. Включи конфиг и перезагрузи Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/raf-coffee /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

5. Выпусти SSL:

```bash
sudo certbot --nginx -d your-domain.ru -d www.your-domain.ru
```

Проверка автообновления:

```bash
systemctl status certbot.timer
```

---

## 8) Обновление приложения

```bash
cd ~/raf-coffee
git pull
docker compose up -d --build
docker image prune -f
```

---

## 9) Полезные команды

Статус контейнеров:

```bash
docker compose ps
```

Логи всех сервисов:

```bash
docker compose logs -f
```

Логи только backend:

```bash
docker compose logs -f backend
```

Перезапуск:

```bash
docker compose restart
```

---

## 10) Мини-чеклист

- Внешне открыты только `22`, `80`, `443`.
- `ADMIN_TOKEN` задан сложный и хранится в `.env`.
- Порты `5432` и `6379` не опубликованы наружу.
- Настроены бэкапы `postgres_data`.
