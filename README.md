# Telegram-бот для каталога vape-товаров (18+)

MVP-бот для Telegram: категории, добавление в корзину и отправка заявки администратору.

> ⚠️ Важно: продажи никотинсодержащей продукции регулируются законом. Используйте бота только при соблюдении локальных требований (включая возрастные ограничения 18+).

## Возможности

- Age-gate 18+ при старте.
- Каталог по категориям:
  - Жижи
  - Электронные сигареты
  - Картриджи
- Добавление товаров в корзину.
- Оформление заявки (уведомление в `ADMIN_CHAT_ID`).
- Список админов по username через `ADMIN_USERNAMES` (по умолчанию включен `cloudmanagerss`).
- Команда `/whoami` показывает ваш Telegram `id`, `username` и админ-статус.

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# заполните BOT_TOKEN, ADMIN_CHAT_ID, ADMIN_USERNAMES и при необходимости PRICE_SOURCE/MINI_APP_URL
python bot.py
```

## Переменные окружения

- `BOT_TOKEN` — токен бота от BotFather.
- `ADMIN_CHAT_ID` — ID чата/пользователя, куда бот отправит заявку.
- `ADMIN_USERNAMES` — список Telegram username администраторов через запятую (например `cloudmanagerss,another_admin`).

## Что можно улучшить дальше

- Хранить каталог в БД.
- Добавить остатки и вариации крепости.
- Подключить оплату.
- Добавить панель администратора.


## Управление ботом

- Найти бота можно по username, который выдаст `@BotFather` при создании.
- Управление в текущем MVP — через команды в Telegram: `/start`, `/help`, `/admin`, `/whoami`, `/app`.
- Для локального запуска заполните `.env` (в репозиторий не коммитится).


## Импорт прайса и наценка

- Укажите `PRICE_SOURCE` в `.env` (локальный путь к `.csv/.json` или URL).
- Для каждой позиции применяется наценка по закупочной цене:
  - до 200 ₽: +80%
  - до 250 ₽: +50%
  - выше 250 ₽: +35%
- Поддерживаемые поля CSV/JSON: `name` (`Наименование`), `purchase_price`/`cost` (`Закуп`/`Цена`), `category` (`Категория`), опционально `sku` (`Артикул`).
- Если прайс недоступен, бот использует встроенный каталог.


## Mini App (Telegram WebApp)

- Задайте `MINI_APP_URL` в `.env` (обязательно `https://`).
- В боте используйте команду `/app` — откроется кнопка запуска mini app.
- Базовая страница mini app лежит в `webapp/index.html`.
- Для продакшена разместите `webapp/` на HTTPS-домене (Vercel/Netlify/Nginx).

## 24/7 запуск

### Вариант 1: Docker Compose

```bash
docker compose up -d --build
```

- Контейнер настроен с `restart: always`, бот поднимется после перезагрузки сервера.

### Вариант 2: systemd (Linux VM)

1. Создайте venv и установите зависимости.
2. Создайте unit `/etc/systemd/system/vape-bot.service`:

```ini
[Unit]
Description=Telegram Vape Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/vape-bot
EnvironmentFile=/opt/vape-bot/.env
ExecStart=/opt/vape-bot/.venv/bin/python /opt/vape-bot/bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

3. Включите автозапуск:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now vape-bot
```


### Ошибка `failed to read dockerfile: open Dockerfile: no such file or directory`

Это значит, что команда запускается не из корня проекта или указан неверный контекст сборки.

Проверьте пошагово:

```bash
cd /workspace/-
ls -la Dockerfile docker-compose.yml
docker compose up -d --build
```

Если запускаете `docker build` вручную, укажите файл явно:

```bash
docker build -t vape-bot -f /workspace/-/Dockerfile /workspace/-
```

## Если нет облака: как запустить на обычном ПК (пошагово)

Ниже самый простой путь, если вы не хотите покупать сервер прямо сейчас.

### Шаг 1. Где взять токен и куда зайти

1. В Telegram откройте `@BotFather`.
2. Нажмите `/newbot` и создайте бота.
3. Скопируйте `BOT_TOKEN`.

### Шаг 2. Подготовить проект на ПК

Откройте терминал в папке проекта (`/workspace/-`) и выполните:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Заполните `.env`:

```env
BOT_TOKEN=ваш_токен_от_BotFather
ADMIN_CHAT_ID=ваш_telegram_id
ADMIN_USERNAMES=cloudmanagerss
```

### Шаг 3. Проверка запуска

```bash
python bot.py
```

Если в консоли нет ошибок — откройте бота в Telegram и отправьте `/start`.

### Шаг 4. Чтобы бот работал 24/7 на ПК

- **Linux**: используйте `systemd` (пример выше в этом README).
- **Windows**: держите запущенным терминал **или** добавьте `python bot.py` в «Планировщик задач» (Task Scheduler) с автозапуском при входе в систему.
- **Важно**: если ПК выключен, спит или пропал интернет — бот не отвечает.

## Бесплатные варианты вместо облака (если ПК неудобно держать включенным)

- **Render / Railway / Koyeb (free tier)** — можно разместить бота без своего сервера.
- На бесплатных тарифах бывают ограничения (сон сервиса, лимиты часов/ресурсов), поэтому для стабильного 24/7 чаще нужен платный тариф.

## Деплой на бесплатный облачный хостинг (Render) — пошагово

Если хотите, чтобы бот работал без включенного ПК, самый простой путь из этого репозитория — Render.

### 1) Подготовьте репозиторий

1. Залейте проект в GitHub (private/public — не важно).
2. Убедитесь, что в репозитории есть `render.yaml` (он уже добавлен в этот проект).
3. Перед деплоем запустите быструю проверку:

```bash
cp .env.example .env
# заполните BOT_TOKEN и ADMIN_CHAT_ID
./scripts_render_preflight.sh
```


### Быстрая настройка окружения (.env)

```bash
./scripts/setup_env.sh
```

Скрипт:
- создаёт `.env` из `.env.example` (если файла ещё нет);
- добавляет недостающие ключи `BOT_TOKEN`, `ADMIN_CHAT_ID`, `ADMIN_USERNAMES`;
- ставит `ADMIN_USERNAMES=cloudmanagerss`, если поле пустое.

После этого откройте `.env` и впишите реальные значения:

```env
BOT_TOKEN=...
ADMIN_CHAT_ID=...
```

И проверьте конфигурацию:

```bash
./scripts_render_preflight.sh
```

### 2) Создайте сервис в Render

1. Зайдите в https://render.com и войдите через GitHub.
2. Нажмите **New +** → **Blueprint**.
3. Выберите ваш репозиторий.
4. Render прочитает `render.yaml` и предложит создать worker `vape-telegram-bot`.
5. Подтвердите создание.

### 3) Заполните переменные окружения в Render

В панели Render откройте ваш worker → **Environment** и задайте:

- `BOT_TOKEN` — токен бота от `@BotFather`.
- `ADMIN_CHAT_ID` — ваш Telegram ID.
- `ADMIN_USERNAMES` — например `cloudmanagerss`.
- `PRICE_SOURCE` — ссылка/путь к прайсу (опционально).
- `MINI_APP_URL` — `https://...` адрес mini app (опционально).

После сохранения Render перезапустит сервис.

### 4) Проверка

1. Откройте **Logs** у worker и убедитесь, что нет ошибок старта.
2. В Telegram откройте вашего бота и отправьте `/start`.
3. Проверьте `/whoami` и `/admin`.




### Сделай это автоматически (одной командой)

Запусти общий чек-лист перед деплоем:

```bash
./scripts/do_render_deploy_checklist.sh
```

Он последовательно проверит:
- `render.yaml` и ветку `main`;
- наличие `requirements.txt`/`bot.py` в корне;
- `.env` и обязательные переменные;
- совпадение локального коммита с `origin/main`.

После этого в Render останется только:
- Branch: `main`
- Blueprint Path: `render.yaml`
- добавить `BOT_TOKEN` и `ADMIN_CHAT_ID`
- нажать **Manual Deploy**

### Ошибка `Blueprint file render.yaml not found on main branch`

Это почти всегда значит одно из двух:
- файл не запушен в GitHub;
- в Render выбрана ветка, где этого файла нет.

Проверьте локально:

```bash
./scripts/check_render_blueprint.sh
```

И затем обязательно запушьте:

```bash
git push -u origin main
```

В Render должно быть:
- **Branch**: `main`
- **Blueprint Path**: `render.yaml`



### Если Render деплоит старый коммит (например `Initialize repository`)

Это значит, что в GitHub/ветке `main` нет ваших последних изменений. Render деплоит только то, что уже запушено.

Проверьте синхронизацию локального и удалённого коммита:

```bash
./scripts/check_render_deploy_commit.sh
```

Если скрипт пишет про старый remote-коммит — выполните:

```bash
git push origin main
```

После push в Render нажмите **Manual Deploy** или дождитесь Auto Deploy.

### Если в Render ошибка `Could not open requirements file: requirements.txt`

Это означает, что Render запускает сборку не из корня проекта (или сервис создан не как Python Blueprint).

Сделайте так:

1. В Render откройте сервис → **Settings**.
2. Проверьте:
   - **Runtime**: `Python`
   - **Root Directory**: пусто или `.`
   - **Build Command**: `python -m pip install -r ./requirements.txt`
   - **Start Command**: `python ./bot.py`
3. Нажмите **Manual Deploy**.

Локальная проверка структуры проекта:

```bash
./scripts/check_render_paths.sh
```

### Если в Render ошибка `failed to read dockerfile`

По скриншоту у вас запускается **Docker build**, а для этого проекта на Render лучше использовать **Blueprint/Python worker** (без Docker runtime).

Сделайте так:

1. В Render удалите текущий сервис, который собирается через Docker (или создайте новый отдельно).
2. Нажмите **New + → Blueprint** и выберите репозиторий с этим проектом.
3. Убедитесь, что Render подхватил `render.yaml` (там `runtime: python`, `rootDir: .`).
4. В `Environment` задайте минимум:
   - `BOT_TOKEN`
   - `ADMIN_CHAT_ID`
5. Нажмите **Manual Deploy**.

Если хотите оставить именно Docker-сервис, проверьте в настройках сервиса:

- **Root Directory** должен указывать на папку, где лежит `Dockerfile`.
- **Dockerfile Path** должен быть `Dockerfile` (или `./Dockerfile`).

### Важно про free тариф

- На бесплатном тарифе могут быть ограничения по времени работы/ресурсам.
- Если нужен максимально стабильный 24/7 без пауз, обычно переходят на платный план.
