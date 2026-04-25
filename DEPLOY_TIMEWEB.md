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

## 5) Прод-override compose (чтобы не ломать локалку)

В репозитории есть отдельный файл `docker-compose.prod.yml`.
Он делает две вещи:
- закрывает наружу порты `postgres`, `redis`, `backend`;
- оставляет `frontend` только на loopback: `127.0.0.1:8080:80`.

Локальная разработка остается прежней:

```bash
docker compose up --build
```

Прод-запуск на VPS:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

---

## 6) Запуск проекта на VPS

```bash
cd ~/raf-coffee
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose ps
```

Проверки на сервере:

```bash
curl http://127.0.0.1:8080
curl http://127.0.0.1:8080/ping
```

---

## 7) Домен и SSL (Let's Encrypt)

### Вариант A (рекомендуется): SSL на хосте через Nginx

1. Установи Nginx и Certbot:

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

2. Настрой DNS у домена в Timeweb:
- `A` для `rafchik.ru` -> `IP_VPS`
- `A` для `www` -> `IP_VPS` (или `CNAME` на `rafchik.ru`)

3. Возьми готовый конфиг из репозитория:
- файл: `deploy/nginx/rafchik.ru.conf`

Скопируй его на сервер:

```bash
sudo cp deploy/nginx/rafchik.ru.conf /etc/nginx/sites-available/rafchik.ru
sudo ln -s /etc/nginx/sites-available/rafchik.ru /etc/nginx/sites-enabled/rafchik.ru
sudo nginx -t
sudo systemctl reload nginx
```

4. Выпусти SSL:

```bash
sudo certbot --nginx -d rafchik.ru -d www.rafchik.ru
```

5. Проверка автообновления сертификатов:

```bash
systemctl status certbot.timer
```

---

## 8) Полезные замечания по безопасности

- Во внешнем фаерволе оставь только `22`, `80`, `443`.
- `ADMIN_TOKEN` обязательно задай в `.env` сложным значением.

---

## 9) Обновление приложения

```bash
cd ~/raf-coffee
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker image prune -f
```

---

## 10) Полезные команды

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

## 11) Мини-чеклист

- Внешне открыты только `22`, `80`, `443`.
- `ADMIN_TOKEN` задан сложный и хранится в `.env`.
- Порты `5432`, `6379`, `8000` не опубликованы наружу.
- `frontend` доступен только локально на сервере (`127.0.0.1:8080`).
- Настроены бэкапы `postgres_data`.
