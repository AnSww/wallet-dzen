# Wallet Dzen 💰

Учебный pet‑проект для демонстрации навыков backend‑разработки на
**Python**.\
Реализован сервис учёта личных финансов с поддержкой категорий, счетов,
транзакций и бюджетов.

## 🚀 Технологии

-   [FastAPI](https://fastapi.tiangolo.com/) --- веб‑фреймворк
-   [SQLAlchemy 2.0 + AsyncIO](https://docs.sqlalchemy.org/) --- работа
    с БД
-   [Alembic](https://alembic.sqlalchemy.org/) --- миграции
-   [Poetry](https://python-poetry.org/) --- менеджер зависимостей
-   [JWT Auth (RS256)](https://jwt.io/) --- аутентификация и авторизация
-   [Docker + docker‑compose](https://docs.docker.com/) ---
    контейнеризация

## 📂 Структура проекта

    wallet-dzen/
    ├── app/                  # основной код приложения
    │   ├── api/              # роутеры FastAPI
    │   ├── core/             # настройки и конфигурация
    │   ├── db/               # база данных и модели
    │   ├── certs/            # ключи для JWT
    │   └── main.py           # точка входа FastAPI
    ├── alembic/              # миграции
    ├── alembic.ini           # конфиг Alembic
    ├── entrypoint.sh         # запуск внутри контейнера
    ├── docker-compose.yml
    ├── Dockerfile
    ├── pyproject.toml
    └── README.md

## ⚙️ Запуск локально (без Docker)

``` bash
# установка зависимостей
poetry install
# прогон миграций
alembic upgrade head
# запуск
uvicorn app.main:app --reload
```

По адрессу <http://localhost:8000/docs> откроется Swagger UI.

## 🐳 Запуск через Docker

``` bash
docker compose up --build
```

После поднятия контейнеров Swagger UI сервиса будет доступен на
<http://localhost:8000/docs>.

## 🔑 Авторизация

Используется JWT (RS256). При старте контейнера автоматически
генерируются ключи, если их нет.\
Регистрация / логин возвращают `access` и `refresh` токены. Оба токена сохраняются в cookie, но также можно Access‑токен
 передавать в `Authorization: Bearer <token>`.

## 📌 Функционал

-   **Пользователи** --- регистрация, аутентификация, роли
-   **Счета** --- добавление и управление счетами
-   **Категории** --- расходы и доходы
-   **Транзакции** --- учёт операций по счетам
-   **Бюджеты** --- планирование трат по категориям с расчётом факта и
    дельты

