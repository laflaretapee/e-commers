import os
import json
from typing import List

import redis.asyncio as redis
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = FastAPI(
    title="Cart Service",
    description="Корзина пользователя на Redis.",
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


redis_client = redis.from_url(REDIS_URL, decode_responses=True)


class CartItem(BaseModel):
    product_id: int = Field(..., ge=1)
    quantity: int = Field(..., ge=1)
    price: float = Field(..., ge=0)  # фиксируем цену на момент добавления


class Cart(BaseModel):
    user_id: int
    items: List[CartItem]


def _cart_key(user_id: int) -> str:
    return f"cart:{user_id}"


async def _load_cart(user_id: int) -> List[CartItem]:
    key = _cart_key(user_id)
    data = await redis_client.get(key)
    if not data:
        return []
    raw_items = json.loads(data)
    return [CartItem(**item) for item in raw_items]


async def _save_cart(user_id: int, items: List[CartItem]) -> None:
    key = _cart_key(user_id)
    await redis_client.set(key, json.dumps([item.model_dump() for item in items]))


@app.get("/")
async def root():
    return {"service": "cart", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/cart", response_model=Cart)
async def get_cart(user_id: int = Query(..., ge=1)):
    items = await _load_cart(user_id)
    return Cart(user_id=user_id, items=items)


@app.post("/cart/add", response_model=Cart)
async def add_to_cart(
    user_id: int = Query(..., ge=1),
    item: CartItem = ...,
):
    items = await _load_cart(user_id)

    for existing in items:
        if existing.product_id == item.product_id and existing.price == item.price:
            existing.quantity += item.quantity
            break
    else:
        items.append(item)

    await _save_cart(user_id, items)
    return Cart(user_id=user_id, items=items)


@app.post("/cart/remove", response_model=Cart)
async def remove_from_cart(
    user_id: int = Query(..., ge=1),
    item: CartItem = ...,
):
    items = await _load_cart(user_id)
    new_items: List[CartItem] = []

    for existing in items:
        if existing.product_id == item.product_id and existing.price == item.price:
            new_qty = existing.quantity - item.quantity
            if new_qty > 0:
                new_items.append(
                    CartItem(
                        product_id=existing.product_id,
                        quantity=new_qty,
                        price=existing.price,
                    )
                )
        else:
            new_items.append(existing)

    await _save_cart(user_id, new_items)
    return Cart(user_id=user_id, items=new_items)


@app.post("/cart/clear", response_model=Cart)
async def clear_cart(user_id: int = Query(..., ge=1)):
    key = _cart_key(user_id)
    await redis_client.delete(key)
    return Cart(user_id=user_id, items=[])
