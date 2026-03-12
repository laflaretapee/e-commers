# Market AI E-Commerce

Учебный e-commerce проект на микросервисной архитектуре с отдельным AI-контуром: рекомендациями, модерацией, event store, feature store и запуском обучения моделей.

## Что внутри

Проект состоит из двух больших частей:

- `backend/` — набор FastAPI-сервисов, PostgreSQL, Redis, Kafka, pgAdmin
- `e-commers-frontend/` — React + Vite интерфейс в стиле Ozon / AI admin console

Система покрывает пользовательский сценарий интернет-магазина и одновременно демонстрирует интеллектуализацию:

- персональные рекомендации товаров
- AI-модерацию карточек
- сбор событий действий пользователя
- обратную связь по рекомендациям
- запуск recommendation training
- реестр моделей и активацию production-модели

## Архитектура

### Сервисы

| Сервис | Порт | Назначение |
| --- | --- | --- |
| `auth_service` | `8001` | Регистрация, вход, список пользователей |
| `catalog_service` | `8002` | Каталог товаров, создание и чтение карточек |
| `cart_service` | `8003` | Корзина пользователя в Redis |
| `order_service` | `8004` | Создание заказов, интеграция с Kafka |
| `notification_service` | `8005` | Подписка на события заказов из Kafka |
| `ai_service` | `8006` | Event Store, Feature Store, рекомендации, модерация, training, model registry |
| `PostgreSQL` | `5432` | Основная БД |
| `pgAdmin` | `5050` | GUI для PostgreSQL |
| `Redis` | `6379` | Корзина |
| `Kafka` | `9092` | Event streaming для заказов |

### Как взаимодействуют сервисы

1. `catalog_service` при создании товара вызывает `ai_service /moderation/check`.
2. После сохранения товара `catalog_service` отправляет item features и AI event.
3. `catalog_service` и `cart_service` запрашивают рекомендации из `ai_service`.
4. `order_service` после оформления заказа отправляет событие и в Kafka, и в `ai_service`.
5. `notification_service` читает заказ из Kafka.
6. `ai_service` копит события, признаки, feedback и использует их для последующего обучения.

## AI-контур

### Реализованные функции

- `Event Store`
  - хранение пользовательских событий в `ai_events`
- `Feature Store`
  - признаки товаров в `item_features`
  - признаки пользователей в `user_features`
- `Recommendations`
  - выдача рекомендаций
  - логирование запросов и результатов
  - прием feedback `clicked / skipped / disliked`
- `Moderation`
  - автоматическая AI-проверка карточки
  - апелляции по решениям модерации
- `Training / MLOps`
  - запуск `recommendation training`
  - хранение training jobs
  - model registry
  - активация production-модели

### Основные AI endpoint-ы

| Endpoint | Назначение |
| --- | --- |
| `POST /events` | Запись AI-события |
| `GET /events` | Просмотр событий |
| `PUT /features/items/{item_id}` | Обновление item features |
| `POST /recommendations` | Выдача рекомендаций |
| `POST /recommendations/feedback` | Фидбек по рекомендациям |
| `POST /moderation/check` | AI-модерация товара |
| `POST /moderation/appeals` | Создание апелляции |
| `POST /training/recommendation/run` | Запуск обучения recommendation-модели |
| `GET /training/jobs` | Список training jobs |
| `GET /models` | Реестр моделей |
| `POST /models/{model_id}/activate` | Активация модели |

## Frontend

Новый frontend уже приведен к полноценной структуре интерфейса.

### Пользовательские страницы

- `/` — каталог
- `/products/:productId` — карточка товара
- `/cart` — корзина
- `/checkout` — оформление заказа
- `/orders` — история заказов
- `/profile` — профиль пользователя
- `/login` — вход
- `/register` — регистрация

### AI admin pages

- `/admin/ai` — dashboard
- `/admin/ai/recommendations` — preview и управление recommendation-моделью
- `/admin/ai/moderation` — AI moderation console
- `/admin/ai/training` — training center

## Структура репозитория

```text
.
├── backend/
│   ├── auth_service/
│   ├── catalog_service/
│   ├── cart_service/
│   ├── order_service/
│   ├── notification_service/
│   ├── ai_service/
│   └── docker-compose.yml
├── e-commers-frontend/
├── scripts/
├── out/
└── PRACTICES_DEMO.md
```

## Быстрый старт

### 1. Поднять backend

Требуется:

- Docker
- Docker Compose v2

Запуск:

```bash
docker compose -f backend/docker-compose.yml up -d --build
```

Проверка health endpoint-ов:

```bash
curl -sS http://127.0.0.1:8001/health
curl -sS http://127.0.0.1:8002/health
curl -sS http://127.0.0.1:8003/health
curl -sS http://127.0.0.1:8004/health
curl -sS http://127.0.0.1:8005/health
curl -sS http://127.0.0.1:8006/health
```

### 2. Поднять frontend

Требуется:

- Node.js 20+
- npm

Запуск:

```bash
cd e-commers-frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Frontend будет доступен на:

```text
http://127.0.0.1:5173
```

Production build:

```bash
cd e-commers-frontend
npm run build
```

## Swagger / UI / Infra

### Swagger

- `http://127.0.0.1:8001/docs` — Auth
- `http://127.0.0.1:8002/docs` — Catalog
- `http://127.0.0.1:8003/docs` — Cart
- `http://127.0.0.1:8004/docs` — Order
- `http://127.0.0.1:8005/docs` — Notification
- `http://127.0.0.1:8006/docs` — AI

### Дополнительно

- `http://127.0.0.1:5173` — Frontend
- `http://127.0.0.1:5050` — pgAdmin

pgAdmin default credentials:

```text
email: admin@admin.com
password: admin
```

## Как наполнить систему данными

### Заполнить каталог товарами

Если каталог пустой, можно автоматически создать товары:

```bash
python3 scripts/populate_catalog_products.py --count 100
```

Скрипт:

- создаёт продавца через `auth_service`
- создаёт товары через `catalog_service`
- автоматически задействует AI-модерацию и event pipeline

### Сгенерировать CSV-данные для AI-сервиса

```bash
python3 scripts/generate_ai_csv_data.py
```

На выходе создаются:

- `out/ai_events.csv`
- `out/rec_requests.csv`
- `out/rec_results.csv`
- `out/rec_feedback.csv`
- `out/moderation_requests.csv`
- `out/moderation_decisions.csv`
- `out/user_features.csv`
- `out/item_features.csv`
- `out/training_jobs.csv`
- `out/model_registry.csv`
- `out/load.sql`

### Уже подготовленные CSV

В `out/` уже лежат готовые CSV-файлы с валидной связностью и объемом данных выше минимальных требований:

| Таблица | Количество строк |
| --- | ---: |
| `ai_events` | 10430 |
| `rec_requests` | 1500 |
| `rec_results` | 15000 |
| `rec_feedback` | 5850 |
| `moderation_requests` | 420 |
| `moderation_decisions` | 420 |
| `user_features` | 600 |
| `item_features` | 1200 |
| `training_jobs` | 45 |
| `model_registry` | 14 |

## Быстрый demo-сценарий

Для сквозной демонстрации реализован отдельный скрипт:

```bash
python3 scripts/demo_intelligence.py
```

Он автоматически проходит цепочку:

1. health-check сервисов
2. регистрация пользователя
3. создание товаров
4. просмотр каталога
5. добавление в корзину
6. оформление заказа
7. запрос рекомендаций
8. отправка feedback
9. проверка AI events и active model

## Отчеты и практики

Проект связан с практиками ПЗ5, ПЗ6 и ПЗ7.

### Готовые артефакты

- `PRACTICES_DEMO.md` — сценарий показа преподавателю
- `out/Отчет_ПЗ5_ГОСТ.docx`
- `out/Отчет_ПЗ6_ГОСТ.docx`
- `out/Отчет_ПЗ7_ГОСТ.docx`

### Скрипты сборки отчетов

```bash
python3 scripts/build_pr5_report_docx.py
python3 scripts/build_pr6_report_docx.py
python3 scripts/build_pr7_report_docx.py
```

## Полезные сценарии запуска

### Полный запуск

```bash
docker compose -f backend/docker-compose.yml up -d --build
cd e-commers-frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

### Перезапуск только frontend

```bash
cd e-commers-frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

### Остановка backend

```bash
docker compose -f backend/docker-compose.yml down
```

### Полная очистка контейнеров и volume

Осторожно: команда удалит данные PostgreSQL volume.

```bash
docker compose -f backend/docker-compose.yml down -v
```

## Технологии

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- Kafka
- Docker Compose

### Frontend

- React 19
- TypeScript
- Vite
- Axios
- React Router

## Статус проекта

Что уже готово:

- микросервисный backend поднят
- AI service интегрирован в каталог, корзину и заказы
- frontend покрывает user flow и AI admin flow
- генерация CSV-данных реализована
- отчеты по практикам сгенерированы

## Что открыть первым

Если нужен быстрый вход в проект, открой по порядку:

1. `http://127.0.0.1:5173`
2. `http://127.0.0.1:8006/docs`
3. `PRACTICES_DEMO.md`

Этого достаточно, чтобы увидеть frontend, AI Swagger и готовый сценарий показа.
