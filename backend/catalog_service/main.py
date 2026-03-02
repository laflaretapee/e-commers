import os
from typing import Any

import httpx
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .db import Base, engine, get_db
from .models import Product
from .schemas import ProductCreate, ProductUpdate, ProductOut

app = FastAPI(
    title="Catalog Service",
    description="Каталог товаров на PostgreSQL.",
    version="1.0.0",
)

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai_service:8000")
AI_TIMEOUT_SECONDS = float(os.getenv("AI_TIMEOUT_SECONDS", "2.5"))

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


async def _post_ai(path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    try:
        async with httpx.AsyncClient(timeout=AI_TIMEOUT_SECONDS) as client:
            response = await client.post(f"{AI_SERVICE_URL}{path}", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        print(f"[catalog_service] AI POST {path} failed: {exc}")
        return None


async def _put_ai(path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    try:
        async with httpx.AsyncClient(timeout=AI_TIMEOUT_SECONDS) as client:
            response = await client.put(f"{AI_SERVICE_URL}{path}", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        print(f"[catalog_service] AI PUT {path} failed: {exc}")
        return None


async def _moderate_product(payload: dict[str, Any]) -> dict[str, Any] | None:
    return await _post_ai("/moderation/check", payload)


async def _sync_product_to_ai(product: Product, event_type: str) -> None:
    await _put_ai(
        f"/features/items/{product.id}",
        {
            "price": product.price,
            "stock": product.stock,
            "features": {
                "title": product.title,
                "seller_id": product.seller_id,
            },
        },
    )
    await _post_ai(
        "/events",
        {
            "event_type": event_type,
            "user_id": product.seller_id,
            "item_id": product.id,
            "payload": {
                "price": product.price,
                "stock": product.stock,
                "title": product.title,
            },
        },
    )


async def _fetch_catalog_recommendations(user_id: int, limit: int) -> list[int]:
    response = await _post_ai(
        "/recommendations",
        {
            "user_id": user_id,
            "context": "catalog",
            "limit": limit,
        },
    )
    if not response:
        return []
    items = response.get("items") or []
    return [int(item["item_id"]) for item in items if "item_id" in item]



@app.on_event("startup")
async def on_startup():
    # создаём таблицу products, если её ещё нет
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
async def root():
    return {"service": "catalog", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    db: AsyncSession = Depends(get_db),
):
    moderation = await _moderate_product(
        {
            "seller_id": product_in.seller_id,
            "title": product_in.title,
            "description": product_in.description,
            "price": product_in.price,
            "payload": {"image_url": product_in.image_url},
        }
    )
    if moderation and moderation.get("decision") == "reject":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"AI moderation rejected product: {moderation.get('reason_code', 'unknown_reason')}",
        )

    db_product = Product(
        title=product_in.title,
        description=product_in.description,
        price=product_in.price,
        stock=product_in.stock,
        seller_id=product_in.seller_id,
        image_url=product_in.image_url,
    )

    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)

    await _sync_product_to_ai(db_product, "CatalogItemCreated")

    return db_product


@app.get("/products", response_model=list[ProductOut])
async def list_products(
    user_id: int | None = Query(default=None, ge=1),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product))
    products = result.scalars().all()

    if user_id and products:
        recommended_ids = await _fetch_catalog_recommendations(user_id, min(len(products), 20))
        if recommended_ids:
            by_id = {product.id: product for product in products}
            ranked = [by_id[item_id] for item_id in recommended_ids if item_id in by_id]
            ranked_ids = {product.id for product in ranked}
            products = ranked + [product for product in products if product.id not in ranked_ids]

    return products


@app.get("/products/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: int,
    user_id: int | None = Query(default=None, ge=1),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Product not found")

    if user_id:
        await _post_ai(
            "/events",
            {
                "event_type": "CatalogViewed",
                "user_id": user_id,
                "item_id": product.id,
                "payload": {
                    "price": product.price,
                    "stock": product.stock,
                },
            },
        )

    return product


@app.put("/products/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Product not found")

    updated_title = product_in.title if product_in.title is not None else product.title
    updated_description = (
        product_in.description if product_in.description is not None else product.description
    )
    updated_price = product_in.price if product_in.price is not None else product.price

    moderation = await _moderate_product(
        {
            "item_id": product.id,
            "seller_id": product.seller_id,
            "title": updated_title,
            "description": updated_description,
            "price": updated_price,
        }
    )
    if moderation and moderation.get("decision") == "reject":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"AI moderation rejected product update: {moderation.get('reason_code', 'unknown_reason')}",
        )

    if product_in.title is not None:
        product.title = product_in.title
    if product_in.description is not None:
        product.description = product_in.description
    if product_in.price is not None:
        product.price = product_in.price
    if product_in.stock is not None:
        product.stock = product_in.stock

    db.add(product)
    await db.commit()
    await db.refresh(product)

    await _sync_product_to_ai(product, "CatalogItemUpdated")

    return product


@app.delete("/products/{product_id}")
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Product not found")

    await db.delete(product)
    await db.commit()

    await _post_ai(
        "/events",
        {
            "event_type": "CatalogItemDeleted",
            "user_id": product.seller_id,
            "item_id": product_id,
            "payload": {},
        },
    )
    await _put_ai(
        f"/features/items/{product_id}",
        {
            "stock": 0,
            "features": {"is_deleted": True},
        },
    )

    return {"detail": "Product deleted"}
