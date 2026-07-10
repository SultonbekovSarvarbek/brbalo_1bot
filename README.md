# Telegram-бот для Instagram-видео

Бот отслеживает сообщения и подписи в Telegram-группе, находит ссылки на
Instagram Reel, публикации, IGTV и Stories, скачивает доступные видео и отвечает
ими на исходное сообщение. Поддерживаются текстовые и скрытые ссылки, а также
несколько ссылок или видео-карусель (до 10 видео).

## 1. Обязательно перевыпустите токен

Токен, отправленный в чат, уже нельзя считать секретным. Откройте `@BotFather`:

1. Выполните `/revoke` и выберите бота.
2. Скопируйте новый токен.
3. Никому его не отправляйте и не добавляйте в Git.

## 2. Настройте доступ к сообщениям группы

По умолчанию Telegram скрывает от ботов обычные сообщения группы. В `@BotFather`:

1. Выполните `/setprivacy`.
2. Выберите бота.
3. Нажмите `Disable`.
4. Если бот уже был в группе, удалите и добавьте его заново.

Вместо отключения Privacy Mode можно назначить бота администратором группы.

## 3. Локальный запуск

Нужны Python 3.10+ и желательно `ffmpeg`.

```bash
cp .env.example .env
```

В `.env` вставьте **новый** токен:

```dotenv
TELEGRAM_BOT_TOKEN=новый_токен_из_BotFather
```

Затем:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Процесс должен работать постоянно. После строки `Starting Instagram Telegram bot`
добавьте бота в группу и отправьте ссылку на Reel или публикацию.

## Запуск на сервере через PM2

На сервере должны быть Python 3.10+, `python3-venv`, `ffmpeg`, Git и PM2.
После подключения по SSH:

```bash
git clone https://github.com/SultonbekovSarvarbek/brbalo_1bot.git
cd brbalo_1bot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
nano .env
```

В `nano` укажите новый токен в `TELEGRAM_BOT_TOKEN`, сохраните файл и запустите:

```bash
pm2 start ecosystem.config.cjs
pm2 save
pm2 startup
```

Команда `pm2 startup` напечатает ещё одну команду с `sudo` — выполните её, затем
ещё раз выполните `pm2 save`. Полезные команды:

```bash
pm2 status
pm2 logs brbalo-instagram-bot
pm2 restart brbalo-instagram-bot
```

Чтобы установить обновления из GitHub:

```bash
git pull
.venv/bin/pip install -r requirements.txt
pm2 restart brbalo-instagram-bot
```

## Запуск в Docker

После создания `.env`:

```bash
docker compose up -d --build
docker compose logs -f bot
```

## Ограничение одной группой

Узнайте ID группы (у супергруппы он обычно имеет вид `-100...`) и задайте:

```dotenv
ALLOWED_CHAT_IDS=-1001234567890
```

Можно перечислить несколько ID через запятую. Пустое значение разрешает работу
во всех чатах, куда добавлен бот.

## Приватные публикации и ограничения Instagram

Без авторизации бот скачивает только доступные Instagram публикации. Если
Instagram требует вход, экспортируйте cookies в Netscape-формате `cookies.txt`
из аккаунта, которому разрешён просмотр, и задайте абсолютный путь:

```dotenv
INSTAGRAM_COOKIES_FILE=/полный/путь/cookies.txt
```

Cookies дают доступ к аккаунту: храните файл как пароль и не коммитьте его.
Для Docker файл надо отдельно примонтировать в контейнер и указать контейнерный
путь. Скачивайте и пересылайте только те материалы, на использование которых у
вас есть разрешение.

## Проверка

```bash
pip install -r requirements-dev.txt
pytest -q
```
