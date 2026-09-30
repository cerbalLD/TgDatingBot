# TgDatingBot

Telegram-бот знакомств на Python: создание и модерация анкет, поиск людей, лайки и мэтчи, жалобы, поддержка, рассылки и платная подписка через Robokassa.

## Возможности

- регистрация и пошаговое создание анкеты;
- загрузка фотографий и видео;
- редактирование, отключение и повторная модерация анкеты;
- поиск анкет с учётом пола, возраста и ближайших городов;
- лайки, дизлайки, взаимные мэтчи и обмен контактами;
- бесплатный дневной лимит просмотров и подписки на 3, 7 или 30 дней;
- платная анонимная публикация анкеты;
- жалобы на сервис и отдельные анкеты;
- панель администратора: модерация, блокировки, ответы поддержки, управление администраторами, рассылки и цены подписок;
- индексация анкет и подбор кандидатов через Elasticsearch;
- локальное хранение основных данных в SQLite.

## Технологии

- Python 3.12;
- aiogram 3;
- SQLAlchemy 2 и SQLite;
- Elasticsearch 8;
- aiohttp;
- Docker Compose.

## Структура проекта

```text
.
├── app/
│   ├── assets/              # статические изображения и видео бота
│   ├── robokassa/           # формирование платежей и HTTP-обработчики
│   ├── scripts/             # служебные скрипты и тестовые данные
│   ├── store/               # модели, репозитории, SQLite и Elasticsearch
│   ├── telegram/            # пользовательские и административные сценарии
│   ├── utilits/             # геокодирование и работа с городами
│   ├── config.py            # загрузка локального config.json
│   ├── main.py              # точка входа
│   └── requirements.txt
└── docker-compose.yml
```

## Быстрый запуск через Docker Compose

1. Создайте бота через [BotFather](https://t.me/BotFather) и получите токен.
2. Скопируйте пример конфигурации:

   ```powershell
   Copy-Item app/config.json.exemple app/config.json
   ```

   В Linux/macOS:

   ```bash
   cp app/config.json.exemple app/config.json
   ```

3. Заполните обязательные параметры в `app/config.json`: как минимум `bot_token`, `list_admin_user_id`, `db_path`, `downloads_path`, `elastic_url` и `elastic_index`.
4. Запустите сервисы:

   ```bash
   docker compose up --build -d
   ```

5. Посмотрите журналы приложения:

   ```bash
   docker compose logs -f app
   ```

Остановить проект можно командой `docker compose down`. Данные Elasticsearch сохраняются в Docker volume `esdata`; SQLite находится по пути из `db_path`.

> В `docker-compose.yml` используется `network_mode: host`. На Linux Elasticsearch доступен приложению по адресу `http://localhost:9200`. При запуске через Docker Desktop убедитесь, что host networking поддерживается и включён.

## Локальный запуск

Нужны Python 3.12 и запущенный Elasticsearch 8.x.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r app/requirements.txt
Copy-Item app/config.json.exemple app/config.json
$env:BASE_PATH = "$(Resolve-Path app)\"
python app/main.py
```

Elasticsearch можно поднять отдельно:

```bash
docker compose up -d elasticsearch
```

## Конфигурация

Приложение читает JSON-файл `${BASE_PATH}config.json`. В контейнере `BASE_PATH` уже установлен в `/usr/src/app/`; при локальном запуске он должен указывать на каталог `app` и оканчиваться разделителем пути.

| Параметр | Назначение |
| --- | --- |
| `bot_token` | Секретный токен Telegram-бота |
| `list_admin_user_id` | Список Telegram ID главных администраторов |
| `db_path` | Путь к SQLite относительно `BASE_PATH`, например `store/db.sqlite` |
| `downloads_path` | Каталог загруженных медиа относительно `BASE_PATH` |
| `free_view_limit` | Дневной лимит анкет без подписки |
| `subscription_price_3_days` | Цена подписки на 3 дня в копейках |
| `subscription_price_7_days` | Цена подписки на 7 дней в копейках |
| `subscription_price_30_days` | Цена подписки на 30 дней в копейках |
| `anonymous_profile_price` | Цена анонимной публикации в копейках |
| `nominatim_user_agent` | Идентификатор приложения для Nominatim |
| `elastic_url` | URL Elasticsearch |
| `elastic_index` | Имя индекса анкет |

Для Robokassa используются `robokassa_merchant_login`, `robokassa_password_1`, `robokassa_password_2`, `robokassa_is_test`, `robokassa_payment_url`, `robokassa_result_host`, `robokassa_result_port` и `robokassa_result_path`.

Для приёма уведомлений Robokassa адрес Result URL должен быть доступен из интернета и вести на путь из `robokassa_result_path`, по умолчанию `/robokassa/result`. В проекте также предусмотрены страницы `/robokassa/success` и `/robokassa/fail`.

## Команды администратора

- `/admin` — открыть панель администратора;
- `/moderate` — получить следующую анкету на модерацию;
- `/support` — получить следующее обращение;
- `/addadmin` и `/deladmin` — добавить или удалить администратора через Telegram-контакт;
- `/setadminlevel <user_id> <0|1>` — изменить уровень доступа;
- `/setprice <3|7|30> <цена_в_рублях>` — изменить цену тарифа.

ID владельцев из `list_admin_user_id` имеют уровень супер-администратора. Не публикуйте этот список без необходимости.

## Безопасность данных

- `app/config.json` предназначен только для локальных секретов и исключён из Git;
- SQLite, загруженные пользовательские медиа и журналы также исключены из Git, поскольку могут содержать персональные данные;
- в репозиторий следует добавлять только шаблоны конфигурации с пустыми значениями секретов;
- если токен или пароль когда-либо попал в коммит, одного удаления файла недостаточно: секрет нужно немедленно перевыпустить и затем очистить историю Git;
- перед публикацией изменений рекомендуется проверить индекс командой `git diff --cached` и запустить специализированный сканер секретов, например Gitleaks.

Не передавайте `config.json`, базу SQLite, содержимое каталогов `downloads` и `log` третьим лицам.
