#!/usr/bin/env python3
"""Populate catalog service with generated products via API."""

from __future__ import annotations

import argparse
import json
import random
import time
import urllib.error
import urllib.request
from typing import Any


DEFAULT_AUTH_URL = "http://127.0.0.1:8001"
DEFAULT_CATALOG_URL = "http://127.0.0.1:8002"


PRODUCT_TEMPLATES: list[dict[str, Any]] = [
    {
        "kind": "Смартфон",
        "brands": ["NovaTech", "Aster", "Polar", "Vertex"],
        "price": (11990, 79990),
        "desc": "Надежный смартфон для повседневных задач, фото и видео.",
    },
    {
        "kind": "Ноутбук",
        "brands": ["Orion", "Lumen", "Atlas", "Quantum"],
        "price": (35990, 139990),
        "desc": "Производительный ноутбук для учебы, работы и мультимедиа.",
    },
    {
        "kind": "Наушники",
        "brands": ["Echo", "Pulse", "Lumen", "Aural"],
        "price": (1990, 24990),
        "desc": "Комфортные наушники с чистым звуком и стабильным соединением.",
    },
    {
        "kind": "Смарт-часы",
        "brands": ["Orion", "Pulse", "Chrono", "Vega"],
        "price": (3990, 34990),
        "desc": "Умные часы для спорта и контроля ежедневной активности.",
    },
    {
        "kind": "Планшет",
        "brands": ["Aster", "NovaTech", "Vertex", "Lumen"],
        "price": (12990, 69990),
        "desc": "Удобный планшет для чтения, работы с документами и развлечений.",
    },
    {
        "kind": "Монитор",
        "brands": ["Vision", "Atlas", "Orion", "Quantum"],
        "price": (7990, 59990),
        "desc": "Качественный монитор с четким изображением и комфортной цветопередачей.",
    },
    {
        "kind": "Клавиатура",
        "brands": ["KeyPro", "Aster", "Pulse", "NovaTech"],
        "price": (1290, 14990),
        "desc": "Эргономичная клавиатура для офиса, учебы и домашнего использования.",
    },
    {
        "kind": "Мышь",
        "brands": ["Clicker", "NovaTech", "Aster", "Pulse"],
        "price": (690, 7990),
        "desc": "Точная компьютерная мышь с удобной формой и надежным сенсором.",
    },
    {
        "kind": "Колонка",
        "brands": ["Echo", "Sonic", "Lumen", "Vega"],
        "price": (1490, 22990),
        "desc": "Портативная колонка для музыки дома и в поездках.",
    },
    {
        "kind": "Роутер",
        "brands": ["NetWave", "Orbit", "Pulse", "Atlas"],
        "price": (1990, 18990),
        "desc": "Стабильный Wi-Fi роутер для квартиры и небольшого офиса.",
    },
    {
        "kind": "Внешний SSD",
        "brands": ["DataCore", "Aster", "Vertex", "Orbit"],
        "price": (2990, 27990),
        "desc": "Быстрый внешний накопитель для хранения файлов и резервных копий.",
    },
    {
        "kind": "Power Bank",
        "brands": ["Volt", "Pulse", "NovaTech", "Orbit"],
        "price": (990, 9990),
        "desc": "Компактный внешний аккумулятор для зарядки гаджетов в дороге.",
    },
]

ADJECTIVES = [
    "компактный",
    "производительный",
    "универсальный",
    "надежный",
    "современный",
    "удобный",
    "функциональный",
    "легкий",
]

FEATURES = [
    "поддержка Bluetooth",
    "энергоэффективная работа",
    "гарантия 12 месяцев",
    "качественная сборка",
    "оперативная отправка",
    "актуальная версия прошивки",
    "простой интерфейс",
    "стабильная работа под нагрузкой",
]


def request_json(method: str, url: str, payload: dict[str, Any] | None = None) -> tuple[int, Any]:
    headers = {}
    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url=url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8") if err.fp else ""
        try:
            data = json.loads(raw)
        except Exception:
            data = raw
        return err.code, data
    except urllib.error.URLError as err:
        return 0, {"detail": str(err.reason)}


def ensure_health(auth_url: str, catalog_url: str) -> None:
    for url in (f"{auth_url}/health", f"{catalog_url}/health"):
        status, body = request_json("GET", url)
        if status != 200:
            raise RuntimeError(f"Health check failed: {url}, status={status}, payload={body}")


def create_seller(auth_url: str) -> int:
    suffix = int(time.time())
    payload = {
        "email": f"catalog_seller_{suffix}@example.com",
        "password": "test12345",
        "full_name": "Catalog Seeder Seller",
        "role": "seller",
    }
    status, body = request_json("POST", f"{auth_url}/register", payload)
    if status >= 400:
        raise RuntimeError(f"Cannot create seller, status={status}, payload={body}")
    return int(body["id"])


def build_product_payload(rng: random.Random, seller_id: int, index: int) -> dict[str, Any]:
    template = rng.choice(PRODUCT_TEMPLATES)
    brand = rng.choice(template["brands"])
    model_code = f"{rng.randint(10, 99)}{chr(rng.randint(65, 90))}"
    adjective = rng.choice(ADJECTIVES)
    feature_a, feature_b = rng.sample(FEATURES, 2)
    price_min, price_max = template["price"]
    price = round(rng.uniform(price_min, price_max), 2)
    stock = rng.randint(3, 120)

    title = f"{template['kind']} {brand} {model_code}"
    description = (
        f"{template['desc']} Это {adjective} вариант модели с акцентом на {feature_a}. "
        f"Дополнительно: {feature_b}. Серия {index + 1}."
    )

    return {
        "title": title,
        "description": description,
        "price": price,
        "stock": stock,
        "seller_id": seller_id,
        "image_url": None,
    }


def populate_products(
    catalog_url: str,
    seller_id: int,
    count: int,
    seed: int,
) -> tuple[int, int]:
    rng = random.Random(seed)
    created = 0
    failed = 0

    for i in range(count):
        payload = build_product_payload(rng, seller_id=seller_id, index=i)
        status, body = request_json("POST", f"{catalog_url}/products", payload)
        if 200 <= status < 300:
            created += 1
        else:
            failed += 1
            print(f"[warn] create failed at #{i + 1}: status={status} payload={body}")

        if (i + 1) % 25 == 0 or i == count - 1:
            print(f"[progress] processed={i + 1}/{count} created={created} failed={failed}")

    return created, failed


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate catalog service with generated products.")
    parser.add_argument("--auth-url", default=DEFAULT_AUTH_URL)
    parser.add_argument("--catalog-url", default=DEFAULT_CATALOG_URL)
    parser.add_argument("--seller-id", type=int, default=None, help="Existing seller id. If omitted, new seller will be created.")
    parser.add_argument("--count", type=int, default=200, help="How many products to create.")
    parser.add_argument("--seed", type=int, default=4322026, help="Random seed for repeatable data.")
    args = parser.parse_args()

    ensure_health(args.auth_url, args.catalog_url)

    seller_id = args.seller_id if args.seller_id else create_seller(args.auth_url)
    if args.seller_id:
        print(f"[info] using existing seller_id={seller_id}")
    else:
        print(f"[info] created seller_id={seller_id}")

    created, failed = populate_products(
        catalog_url=args.catalog_url,
        seller_id=seller_id,
        count=max(1, args.count),
        seed=args.seed,
    )
    print(
        json.dumps(
            {
                "seller_id": seller_id,
                "requested": max(1, args.count),
                "created": created,
                "failed": failed,
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    if created == 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
