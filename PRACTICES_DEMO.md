# Показ функций по практикам

Этот файл нужен как единый сценарий показа преподавателю того, что реализовано в проекте по практикам ПЗ5, ПЗ6 и ПЗ7.

## Что реализовано

### ПЗ5. Генерация и загрузка тестовых данных

Реализован генератор CSV-данных для AI-контура:

- `ai_events` — 10430 строк
- `rec_requests` — 1500 строк
- `rec_results` — 15000 строк
- `rec_feedback` — 5850 строк
- `moderation_requests` — 420 строк
- `moderation_decisions` — 420 строк
- `user_features` — 600 строк
- `item_features` — 1200 строк
- `training_jobs` — 45 строк
- `model_registry` — 14 строк

Готовые файлы лежат в `out/`:

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

Скрипт генерации:

- `scripts/generate_ai_csv_data.py`

### ПЗ6. Реализация интеллектуализации

В систему добавлен `ai_service`, который отвечает за:

- сбор событий пользователей
- хранение признаков товаров и пользователей
- персональные рекомендации
- прием обратной связи по рекомендациям
- AI-модерацию карточек товаров
- апелляции по модерации
- запуск обучения модели рекомендаций
- регистрацию и активацию моделей

Также связаны остальные сервисы:

- `auth_service` — регистрация и вход
- `catalog_service` — товары, AI-модерация, показ каталога с учетом рекомендаций
- `cart_service` — корзина и рекомендации в корзине
- `order_service` — заказ из корзины, отправка события в Kafka и AI
- `notification_service` — чтение событий заказов из Kafka
- `e-commers-frontend` — пользовательский интерфейс

### ПЗ7. Use case и показ сценариев

В проекте покрыты сценарии:

- `UC-AI1` — получить персональные рекомендации
- `UC-AI2` — дать фидбек по рекомендациям
- `UC-AI3` — проверить карточку товара
- `UC-AI4` — оспорить решение модерации
- `UC-AI5` — просмотреть статистику модели
- `UC-AI6` — запустить обучение модели
- `UC-AI7` — переобучить рекомендации на новых данных

## Что открыть на показе

### Swagger

- `http://127.0.0.1:8001/docs` — Auth Service
- `http://127.0.0.1:8002/docs` — Catalog Service
- `http://127.0.0.1:8003/docs` — Cart Service
- `http://127.0.0.1:8004/docs` — Order Service
- `http://127.0.0.1:8005/docs` — Notification Service
- `http://127.0.0.1:8006/docs` — AI Service

### Frontend

- `http://127.0.0.1:5173`

## Как запустить

### Backend

```bash
docker compose -f backend/docker-compose.yml up -d --build
```

### Frontend

```bash
cd e-commers-frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

### Если каталог пустой

```bash
python3 scripts/populate_catalog_products.py --count 100
```

### Быстрый сквозной прогон

```bash
python3 scripts/demo_intelligence.py
```

## Рекомендуемый порядок показа

### 1. Показать, что все сервисы подняты

Открыть `GET /health` в:

- Auth
- Catalog
- Cart
- Order
- Notification
- AI

Итог: у всех должен быть ответ `{"status":"ok"}`.

### 2. Показать регистрацию и вход

В `Auth Service`:

- `POST /register`
- `POST /login`
- `GET /users`

Тело для `POST /register`:

```json
{
  "email": "demo_pz_user@example.com",
  "password": "test12345",
  "full_name": "Demo Practice User",
  "role": "customer"
}
```

Тело для `POST /login`:

```json
{
  "email": "demo_pz_user@example.com",
  "password": "test12345"
}
```

Что говорить:

- пользователь создается в PostgreSQL
- логин возвращает данные пользователя
- `id` пользователя потом используется в AI-сценариях

### 3. Показать создание товаров и AI-модерацию

В `Catalog Service`:

- `POST /products`
- `GET /products`

Тело для `POST /products`:

```json
{
  "title": "Смарт-часы Orion Active",
  "description": "Удобные часы для спорта и повседневного использования.",
  "price": 8990,
  "stock": 25,
  "seller_id": 1,
  "image_url": null
}
```

Еще один товар:

```json
{
  "title": "Наушники Lumen Air",
  "description": "Беспроводные наушники с шумоподавлением и чистым звуком.",
  "price": 4990,
  "stock": 40,
  "seller_id": 1,
  "image_url": null
}
```

Что здесь реально происходит:

- `catalog_service` вызывает `ai_service /moderation/check`
- если решение не `reject`, товар сохраняется
- затем товар отправляется в `ai_service /features/items/{item_id}`
- затем создается событие `CatalogItemCreated` через `ai_service /events`

### 4. Показать прямую AI-модерацию в Swagger

В `AI Service` открыть:

- `POST /moderation/check`

Тело запроса с успешной публикацией:

```json
{
  "item_id": 999,
  "seller_id": 1,
  "title": "Чехол для смартфона SoftCase",
  "description": "Прочный чехол из силикона с мягкими бортами и точными вырезами.",
  "category_id": 12,
  "price": 790,
  "payload": {
    "color": "black",
    "material": "silicone"
  }
}
```

Тело запроса, которое должно уйти в `reject`:

```json
{
  "item_id": 1000,
  "seller_id": 1,
  "title": "Ставки casino premium",
  "description": "Переходите на сайт и смотрите подробности.",
  "category_id": 12,
  "price": 500,
  "payload": {}
}
```

Что говорить:

- модерация работает rule-based через `BANNED_PATTERNS`
- сервис возвращает `publish`, `manual_review` или `reject`
- решение и причина сохраняются в таблицах модерации

### 5. Показать каталог и просмотр товара

В `Catalog Service`:

- `GET /products`
- `GET /products/{product_id}?user_id=1`

Что говорить:

- список товаров можно открыть и без пользователя
- если передан `user_id`, каталог пытается ранжироваться AI-рекомендациями
- при открытии карточки товара отправляется событие `CatalogViewed`

### 6. Показать рекомендации

В `AI Service`:

- `POST /recommendations`
- `GET /recommendations`

Тело для `POST /recommendations`:

```json
{
  "user_id": 1,
  "context": "catalog",
  "category_id": null,
  "item_id": null,
  "item_ids": [],
  "limit": 5,
  "ab_bucket": "demo"
}
```

Что показать в ответе:

- `request_id`
- `model_version`
- `latency_ms`
- список `items` со `score` и `reason`

Что говорить:

- запрос логируется в `rec_requests`
- результаты пишутся в `rec_results`
- одновременно в `ai_events` сохраняется событие `RecommendationShown`

### 7. Показать обратную связь по рекомендациям

Сначала взять из ответа предыдущего шага:

- `request_id`
- `items[0].item_id`

Далее вызвать `POST /recommendations/feedback`.

Тело с кликом:

```json
{
  "request_id": 1,
  "user_id": 1,
  "item_id": 2,
  "action": "clicked",
  "payload": {
    "source": "swagger_demo"
  }
}
```

Тело с негативным фидбеком:

```json
{
  "request_id": 1,
  "user_id": 1,
  "item_id": 3,
  "action": "disliked",
  "payload": {
    "source": "swagger_demo"
  }
}
```

Что говорить:

- фидбек пишется в `rec_feedback`
- дополнительно создается AI-событие
- счетчики признаков товара и пользователя обновляются
- эти данные затем участвуют в обучении

### 8. Показать корзину и рекомендации внутри корзины

В `Cart Service`:

- `POST /cart/add?user_id=1`
- `GET /cart?user_id=1`
- `POST /cart/remove?user_id=1`
- `POST /cart/clear?user_id=1`

Тело для `POST /cart/add`:

```json
{
  "product_id": 1,
  "quantity": 1,
  "price": 8990
}
```

Что говорить:

- корзина хранится в Redis
- при добавлении создается событие `AddToCart`
- после этого `cart_service` запрашивает AI-рекомендации в контексте `cart`

### 9. Показать создание заказа

В `Order Service`:

- `POST /orders/from-cart?user_id=1`
- `GET /orders?user_id=1`

Для `POST /orders/from-cart` тело не нужно.

Что говорить:

- заказ сохраняется в PostgreSQL
- событие заказа отправляется в Kafka
- `notification_service` читает это событие
- в AI отправляется `OrderCreated`, который влияет на обучение рекомендаций

### 10. Показать журнал AI-событий

В `AI Service`:

- `GET /events?user_id=1&limit=100`

Что нужно увидеть:

- `CatalogItemCreated`
- `CatalogViewed`
- `RecommendationShown`
- `RecommendationClicked`
- `AddToCart`
- `OrderCreated`

Это лучший технический пруф, что интеллектуальный контур реально связан с остальной системой.

### 11. Показать обучение модели рекомендаций

В `AI Service`:

- `POST /training/recommendation/run`
- `GET /training/jobs`
- `GET /models/active?model_type=recommendation`
- `GET /models`

Тело для запуска обучения:

```json
{
  "lookback_days": 90,
  "max_samples": 1000,
  "min_samples": 10,
  "epochs": 5,
  "learning_rate": 0.03,
  "l2": 0.001,
  "min_positive_samples": 1,
  "activate_model": true,
  "random_seed": 4322026
}
```

Что говорить:

- обучение идет не на заглушке, а на накопленных `rec_results` и `rec_feedback`
- строится обучающая выборка по фактам показа и реакции пользователя
- модель получает новый `model_version`
- активная модель переключается через `is_active`

### 12. Показать реестр моделей и ручное управление

В `AI Service`:

- `POST /models/register`
- `POST /models/{model_id}/activate`

Тело для ручной регистрации модели:

```json
{
  "model_type": "moderation",
  "model_version": "moderation-manual-v1",
  "metrics": {
    "precision": 0.91,
    "recall": 0.88
  },
  "artifact_uri": "s3://models/moderation-manual-v1",
  "is_active": false
}
```

Что говорить:

- это MLOps-часть системы
- модели регистрируются отдельно от запуска inference
- активную модель можно переключить через отдельный endpoint

### 13. Показать апелляции модерации

В `AI Service`:

- `POST /moderation/appeals`
- `POST /moderation/appeals/{appeal_id}/result`

Тело для создания апелляции:

```json
{
  "request_id": 1,
  "seller_id": 1,
  "reason": "Прошу повторно проверить карточку, описание соответствует правилам."
}
```

Тело для результата апелляции:

```json
{
  "reviewer_id": 1001,
  "result": "reverted",
  "notes": "После ручной проверки ограничение снято."
}
```

Что говорить:

- сценарий use case закрывается не только автоматической модерацией
- предусмотрена ручная валидация решения

## Что показать на фронтенде

На `http://127.0.0.1:5173` показать:

1. страницу каталога
2. регистрацию
3. вход
4. корзину
5. оформление заказа
6. страницу заказов

Что проговорить:

- фронтенд работает поверх тех же backend-сервисов
- каталог отображает реальные данные из `catalog_service`
- после входа доступны корзина и заказы
- AI-функции работают не отдельно, а встроены в пользовательский сценарий

## Как связать это с use case ПЗ7

| Use case | Что показывать |
| --- | --- |
| `UC-AI1` | `POST /recommendations` |
| `UC-AI2` | `POST /recommendations/feedback` |
| `UC-AI3` | `POST /moderation/check` |
| `UC-AI4` | `POST /moderation/appeals` и `POST /moderation/appeals/{appeal_id}/result` |
| `UC-AI5` | `GET /models`, `GET /models/active`, `GET /training/jobs` |
| `UC-AI6` | `POST /training/recommendation/run` |
| `UC-AI7` | повторный запуск `POST /training/recommendation/run` после накопления новых событий и фидбека |

## Что сказать в конце показа

Короткая финальная формулировка:

> В проекте реализован отдельный AI-сервис, интегрированный с каталогом, корзиной, заказами и модерацией.  
> Данные для практики сгенерированы в CSV и могут быть загружены в PostgreSQL.  
> Рекомендации, события, обратная связь, обучение и реестр моделей работают как единая подсистема, а сценарии use case из ПЗ7 подтверждаются вызовами через Swagger и фронтенд.

## Полезные файлы

- `scripts/generate_ai_csv_data.py`
- `scripts/populate_catalog_products.py`
- `scripts/demo_intelligence.py`
- `out/Отчет_ПЗ5_ГОСТ.docx`
- `out/Отчет_ПЗ6_ГОСТ.docx`
- `out/Отчет_ПЗ7_ГОСТ.docx`
