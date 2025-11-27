from fastapi import FastAPI, Depends, HTTPException, status
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

    return db_product


@app.get("/products", response_model=list[ProductOut])
async def list_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product))
    products = result.scalars().all()
    return products


@app.get("/products/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Product not found")
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

    return {"detail": "Product deleted"}
