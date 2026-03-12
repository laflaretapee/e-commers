#!/usr/bin/env python3
"""Quick live demo for AI-intellectualization features in mini-ozon."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter


BASE = {
    "auth": "http://127.0.0.1:8001",
    "catalog": "http://127.0.0.1:8002",
    "cart": "http://127.0.0.1:8003",
    "order": "http://127.0.0.1:8004",
    "ai": "http://127.0.0.1:8006",
}


def req(method: str, url: str, payload: dict | None = None) -> tuple[int, object]:
    headers = {}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(url=url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = body
            return response.status, parsed
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8") if err.fp else ""
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw
        return err.code, parsed
    except urllib.error.URLError as err:
        return 0, {"detail": str(err.reason)}


def assert_ok(status: int, data: object, hint: str) -> None:
    if status == 0:
        raise RuntimeError(f"{hint} failed: service unavailable, payload={data}")
    if status >= 400:
        raise RuntimeError(f"{hint} failed: HTTP {status}, payload={data}")


def main() -> None:
    print("== 1) Health checks ==")
    for name, base in BASE.items():
        status, body = req("GET", f"{base}/health")
        assert_ok(status, body, f"health {name}")
        print(f"[ok] {name}: {body}")

    suffix = int(time.time())
    email = f"teacher_demo_{suffix}@example.com"

    print("\n== 2) Register demo user ==")
    status, user = req(
        "POST",
        f"{BASE['auth']}/register",
        {
            "email": email,
            "password": "test12345",
            "full_name": "Teacher Demo User",
            "role": "customer",
        },
    )
    assert_ok(status, user, "register")
    user_id = int(user["id"])  # type: ignore[index]
    print(f"[ok] user_id={user_id}, email={email}")

    print("\n== 3) AI moderation + product creation ==")
    products: list[dict] = []
    product_payloads = [
        {
            "title": "Смарт-часы Orion Active",
            "description": "Удобные часы для повседневного использования и спорта.",
            "price": 8990.0,
            "stock": 25,
            "seller_id": user_id,
            "image_url": None,
        },
        {
            "title": "Наушники Lumen Air",
            "description": "Беспроводные наушники с чистым звуком и долгой автономностью.",
            "price": 4990.0,
            "stock": 30,
            "seller_id": user_id,
            "image_url": None,
        },
    ]

    for payload in product_payloads:
        status, body = req("POST", f"{BASE['catalog']}/products", payload)
        assert_ok(status, body, "create product (moderation)")
        products.append(body)  # type: ignore[arg-type]
        print(f"[ok] product_id={body['id']} title={body['title']}")  # type: ignore[index]

    print("\n== 4) Personalized catalog + view event ==")
    query = urllib.parse.urlencode({"user_id": user_id})
    status, catalog = req("GET", f"{BASE['catalog']}/products?{query}")
    assert_ok(status, catalog, "catalog personalized list")
    print(f"[ok] products in personalized list: {len(catalog)}")  # type: ignore[arg-type]

    first_product_id = int(products[0]["id"])
    status, product = req("GET", f"{BASE['catalog']}/products/{first_product_id}?{query}")
    assert_ok(status, product, "product detail with view event")
    print(f"[ok] opened product {product['id']} -> CatalogViewed sent to AI")  # type: ignore[index]

    print("\n== 5) Cart events + recommendations ==")
    status, cart_after_add = req(
        "POST",
        f"{BASE['cart']}/cart/add?{query}",
        {"product_id": first_product_id, "quantity": 1, "price": products[0]["price"]},
    )
    assert_ok(status, cart_after_add, "cart add")
    print(f"[ok] cart items after add: {len(cart_after_add['items'])}")  # type: ignore[index]

    status, cart_state = req("GET", f"{BASE['cart']}/cart?{query}")
    assert_ok(status, cart_state, "cart get")
    recs_in_cart = cart_state.get("recommendations", [])  # type: ignore[assignment]
    print(f"[ok] cart recommendations: {len(recs_in_cart)}")

    print("\n== 6) Order creation -> AI training event ==")
    status, order = req("POST", f"{BASE['order']}/orders/from-cart?{query}")
    assert_ok(status, order, "create order from cart")
    order_id = int(order["id"])  # type: ignore[index]
    print(f"[ok] order_id={order_id} created; OrderCreated sent to AI")

    print("\n== 7) Direct AI recommendations + feedback ==")
    status, ai_recs = req("GET", f"{BASE['ai']}/recommendations?user_id={user_id}&context=catalog&limit=5")
    assert_ok(status, ai_recs, "ai recommendations")
    print(f"[ok] ai request_id={ai_recs['request_id']}, items={len(ai_recs['items'])}")  # type: ignore[index]

    feedback_sent = 0
    if ai_recs["items"]:  # type: ignore[index]
        top_item = ai_recs["items"][0]["item_id"]  # type: ignore[index]
        status, _ = req(
            "POST",
            f"{BASE['ai']}/recommendations/feedback",
            {
                "request_id": ai_recs["request_id"],  # type: ignore[index]
                "user_id": user_id,
                "item_id": top_item,
                "action": "clicked",
                "payload": {"source": "teacher_demo"},
            },
        )
        assert_ok(status, _, "feedback clicked")
        feedback_sent += 1
    print(f"[ok] feedback events sent: {feedback_sent}")

    print("\n== 8) Verify event trace in AI ==")
    status, events = req("GET", f"{BASE['ai']}/events?user_id={user_id}&limit=100")
    assert_ok(status, events, "ai events by user")
    event_types = Counter(event["event_type"] for event in events)  # type: ignore[arg-type]
    print(f"[ok] total ai events for user={user_id}: {len(events)}")  # type: ignore[arg-type]
    print("event types:", dict(event_types))

    print("\n== 9) MLOps endpoints ==")
    status, model = req("GET", f"{BASE['ai']}/models/active?model_type=recommendation")
    assert_ok(status, model, "active recommendation model")
    print(f"[ok] active rec model: {model['model_version']}")  # type: ignore[index]
    status, jobs = req("GET", f"{BASE['ai']}/training/jobs?limit=5")
    assert_ok(status, jobs, "training jobs list")
    print(f"[ok] training jobs returned: {len(jobs)}")  # type: ignore[arg-type]

    print("\nDEMO COMPLETED SUCCESSFULLY")
    print(
        json.dumps(
            {
                "user_id": user_id,
                "order_id": order_id,
                "ai_events": dict(event_types),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"DEMO FAILED: {exc}")
        print("Hint: docker compose -f backend/docker-compose.yml up -d")
        raise SystemExit(1)
