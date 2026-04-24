# Деплой `raf-coffee` на VPS Timeweb

Ниже пошаговая инструкция для деплоя **текущего** проекта на VPS (Ubuntu 22.04) с `Nginx + Uvicorn + systemd + SSL (Let's Encrypt)`.

## 1) Подготовка VPS

Подключение:

```bash
ssh root@IP_СЕРВЕРА
```

Обновление системы:

```bash
apt update && apt upgrade -y
```

Создание отдельного пользователя:

```bash
adduser deploy
usermod -aG sudo deploy
```

Рекомендация: настроить вход по SSH-ключу и отключить парольный логин для `root`.

---

## 2) Установка пакетов

```bash
apt install -y git python3 python3-venv python3-pip nginx certbot python3-certbot-nginx
```

Если фронтенд собирается через Node/Tailwind:

```bash
apt install -y nodejs npm
```

---

## 3) Клонирование проекта

```bash
su - deploy
git clone <URL_ТВОЕГО_РЕПО> raf-coffee
cd raf-coffee
```

---

## 4) Подготовка backend

```bash
cd ~/raf-coffee/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install fastapi uvicorn asyncpg redis pydantic-settings python-multipart
```

Создай `.env` на основе примера:

```bash
cp .env.example .env
```

И укажи реальные значения для:
- `DATABASE_URL`
- `REDIS_URL`
- `ADMIN_TOKEN`

Проверка запуска вручную:

```bash
cd ~/raf-coffee/backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Проверка: `http://127.0.0.1:8000/ping` должен вернуть JSON со статусом `ok`.

---

## 5) Настройка systemd

Создай файл:

`/etc/systemd/system/raf-coffee.service`

```ini
[Unit]
Description=Raf Coffee Backend
After=network.target

[Service]
User=deploy
Group=www-data
WorkingDirectory=/home/deploy/raf-coffee/backend
Environment="PATH=/home/deploy/raf-coffee/backend/.venv/bin"
ExecStart=/home/deploy/raf-coffee/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Применение:

```bash
sudo systemctl daemon-reload
sudo systemctl enable raf-coffee
sudo systemctl start raf-coffee
sudo systemctl status raf-coffee
```

---

## 6) Настройка Nginx

Создай файл:

`/etc/nginx/sites-available/raf-coffee`

```nginx
server {
    listen 80;
    server_name your-domain.ru www.your-domain.ru;

    client_max_body_size 50M;

    location /static/ {
        alias /home/deploy/raf-coffee/backend/static/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Включение конфига:

```bash
sudo ln -s /etc/nginx/sites-available/raf-coffee /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 7) Домен и SSL

1. В DNS добавь `A`-запись на IP VPS.
2. Выпусти сертификат:

```bash
sudo certbot --nginx -d your-domain.ru -d www.your-domain.ru
```

Проверка автообновления:

```bash
systemctl status certbot.timer
```

---

## 8) Обновление приложения (после новых коммитов)

```bash
cd ~/raf-coffee
git pull
cd backend
source .venv/bin/activate
pip install fastapi uvicorn asyncpg redis pydantic-settings python-multipart

sudo systemctl restart raf-coffee
```

---

## 9) Полезные команды диагностики

Логи сервиса:

```bash
journalctl -u raf-coffee -f
```

Логи Nginx:

```bash
sudo tail -f /var/log/nginx/error.log
```

---

## 10) Чеклист безопасности и стабильности

- Открыты только нужные порты (`22`, `80`, `443`).
- Секреты вынесены в `.env`, не хранятся в Git.
- Настроены бэкапы базы данных.
- Проверен автозапуск сервиса после перезагрузки VPS.
