import os
import json
from typing import Any
from typing import List

import httpx
import redis.asyncio as redis
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai_service:8000")
AI_TIMEOUT_SECONDS = float(os.getenv("AI_TIMEOUT_SECONDS", "2.5"))

app = FastAPI(
    title="Cart Service",
    description="Корзина пользователя на Redis.",
    version="1.0.0",
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


redis_client = redis.from_url(REDIS_URL, decode_responses=True)


async def _post_ai(path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    try:
        async with httpx.AsyncClient(timeout=AI_TIMEOUT_SECONDS) as client:
            response = await client.post(f"{AI_SERVICE_URL}{path}", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        print(f"[cart_service] AI POST {path} failed: {exc}")
        return None


class CartItem(BaseModel):
    product_id: int = Field(..., ge=1)
    quantity: int = Field(..., ge=1)
    price: float = Field(..., ge=0)  # фиксируем цену на момент добавления


class RecommendationItem(BaseModel):
    item_id: int
    score: float
    reason: str | None = None


class Cart(BaseModel):
    user_id: int
    items: List[CartItem]
    recommendations: list[RecommendationItem] = Field(default_factory=list)


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


async def _send_cart_event(
    event_type: str,
    user_id: int,
    item: CartItem,
) -> None:
    await _post_ai(
        "/events",
        {
            "event_type": event_type,
            "user_id": user_id,
            "item_id": item.product_id,
            "payload": {
                "quantity": item.quantity,
                "price": item.price,
            },
        },
    )


async def _fetch_cart_recommendations(user_id: int, items: List[CartItem]) -> list[RecommendationItem]:
    if not items:
        return []

    response = await _post_ai(
        "/recommendations",
        {
            "user_id": user_id,
            "context": "cart",
            "item_ids": [item.product_id for item in items],
            "limit": 8,
        },
    )
    if not response:
        return []

    recommendations = []
    for item in response.get("items") or []:
        try:
            recommendations.append(RecommendationItem(**item))
        except Exception:
            continue
    return recommendations


@app.get("/")
async def root():
    return {"service": "cart", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/cart", response_model=Cart)
async def get_cart(user_id: int = Query(..., ge=1)):
    items = await _load_cart(user_id)
    recommendations = await _fetch_cart_recommendations(user_id, items)
    return Cart(user_id=user_id, items=items, recommendations=recommendations)


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
    await _send_cart_event("AddToCart", user_id, item)

    recommendations = await _fetch_cart_recommendations(user_id, items)
    return Cart(user_id=user_id, items=items, recommendations=recommendations)


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
    await _send_cart_event("RemoveFromCart", user_id, item)

    recommendations = await _fetch_cart_recommendations(user_id, new_items)
    return Cart(user_id=user_id, items=new_items, recommendations=recommendations)


@app.post("/cart/clear", response_model=Cart)
async def clear_cart(user_id: int = Query(..., ge=1)):
    key = _cart_key(user_id)
    await redis_client.delete(key)
    return Cart(user_id=user_id, items=[], recommendations=[])
