import os
import json
from typing import List, Optional

import redis.asyncio as redis
from aiokafka import AIOKafkaProducer
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .db import Base, engine, get_db
from .models import Order, OrderItem
from .schemas import CartItem, OrderOut, OrderItemOut

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_ORDERS_TOPIC = os.getenv("KAFKA_ORDERS_TOPIC", "orders")

app = FastAPI(
    title="Order Service",
    description="Заказы: Postgres + Redis Cart + Kafka Events.",
    version="1.0.0",
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Redis-клиент создаём один раз глобально
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Kafka producer создаём на старте
kafka_producer: Optional[AIOKafkaProducer] = None


def _cart_key(user_id: int) -> str:
    return f"cart:{user_id}"


async def _load_cart(user_id: int) -> List[CartItem]:
    key = _cart_key(user_id)
    data = await redis_client.get(key)
    if not data:
        return []
    raw_items = json.loads(data)
    return [CartItem(**item) for item in raw_items]


async def _clear_cart(user_id: int) -> None:
    key = _cart_key(user_id)
    await redis_client.delete(key)


@app.on_event("startup")
async def on_startup():
    global kafka_producer

    # создаём таблицы orders и order_items
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Kafka producer
    kafka_producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    await kafka_producer.start()


@app.on_event("shutdown")
async def on_shutdown():
    global kafka_producer
    if kafka_producer:
        await kafka_producer.stop()


@app.get("/")
async def root():
    return {"service": "order", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/orders/from-cart", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order_from_cart(
    user_id: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
):
    # 1. Читаем корзину из Redis
    items = await _load_cart(user_id)
    if not items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # 2. Считаем сумму
    total_amount = sum(item.price * item.quantity for item in items)

    # 3. Создаём заказ и позиции заказа в БД
    db_order = Order(
        user_id=user_id,
        status="created",
        total_amount=total_amount,
    )
    db.add(db_order)
    await db.flush()  # получаем id заказа до коммита

    for item in items:
        db_item = OrderItem(
            order_id=db_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.price,
        )
        db.add(db_item)

    await db.commit()

    # 4. ЯВНО читаем items через select(), без lazy-load
    result_items = await db.execute(
        select(OrderItem).where(OrderItem.order_id == db_order.id)
    )
    db_items = result_items.scalars().all()

    # 5. Отправляем событие в Kafka (если вдруг Kafka не доступна — не падаем)
    if kafka_producer:
        event = {
            "order_id": db_order.id,
            "user_id": user_id,
            "total_amount": total_amount,
            "status": "created",
            "items": [item.model_dump() for item in items],
        }
        try:
            await kafka_producer.send_and_wait(KAFKA_ORDERS_TOPIC, event)
        except Exception as e:
            print(f"[order_service] Kafka send error: {e}")

    # 6. Очищаем корзину
    await _clear_cart(user_id)

    # 7. Формируем ответ из того, что в БД
    return OrderOut(
        id=db_order.id,
        user_id=user_id,
        status="created",
        total_amount=total_amount,
        created_at=db_order.created_at,
        items=[
            OrderItemOut(
                id=i.id,
                product_id=i.product_id,
                quantity=i.quantity,
                price=i.price,
            )
            for i in db_items
        ],
    )


@app.get("/orders", response_model=list[OrderOut])
async def list_orders(
    user_id: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.user_id == user_id))
    orders = result.scalars().all()
    if not orders:
        return []

    order_ids = [o.id for o in orders]

    result_items = await db.execute(
        select(OrderItem).where(OrderItem.order_id.in_(order_ids))
    )
    items_by_order: dict[int, list[OrderItem]] = {}
    for item in result_items.scalars().all():
        items_by_order.setdefault(item.order_id, []).append(item)

    output: list[OrderOut] = []
    for order in orders:
        db_items = items_by_order.get(order.id, [])
        output.append(
            OrderOut(
                id=order.id,
                user_id=order.user_id,
                status=order.status,
                total_amount=order.total_amount,
                created_at=order.created_at,
                items=[
                    OrderItemOut(
                        id=i.id,
                        product_id=i.product_id,
                        quantity=i.quantity,
                        price=i.price,
                    )
                    for i in db_items
                ],
            )
        )

    return output


@app.get("/orders/{order_id}", response_model=OrderOut)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    result_items = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id)
    )
    db_items = result_items.scalars().all()

    return OrderOut(
        id=order.id,
        user_id=order.user_id,
        status=order.status,
        total_amount=order.total_amount,
        created_at=order.created_at,
        items=[
            OrderItemOut(
                id=i.id,
                product_id=i.product_id,
                quantity=i.quantity,
                price=i.price,
            )
            for i in db_items
        ],
    )
