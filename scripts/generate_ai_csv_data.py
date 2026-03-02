#!/usr/bin/env python3
"""Generate realistic CSV seed data for AI-service tables with validation."""

from __future__ import annotations

import csv
import json
import random
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Deterministic output
SEED = 432_2026

# Volumes (all are >= requested minimums)
N_USERS = 600
N_ITEMS = 1200
N_REC_REQUESTS = 1500
RESULTS_PER_REQUEST = 10
N_MOD_REQUESTS = 420
N_TRAINING_JOBS = 45
N_MODELS_RECS = 8
N_MODELS_MOD = 6

# Additional event volumes for ai_events realism
N_CATALOG_VIEWS = 3600
N_ADD_TO_CART = 1200
N_ORDER_CREATED = 420
N_ORDER_PAID = 260

# Feedback ratios from total shown results
CLICK_RATIO_TARGET = 0.20
DISLIKE_RATIO_TARGET = 0.03
SKIP_RATIO_TARGET = 0.16

OUT_DIR = Path("out")

CONTEXT_VALUES = {"catalog", "item", "cart"}
TRAINING_STATUS_VALUES = {"queued", "running", "failed", "succeeded", "canceled"}
MODEL_TYPE_VALUES = {"recs_ranking", "moderation"}

REASON_CODES = ["similar_items", "popular", "price_drop", "new_arrival", "complementary"]
MOD_REASON_MANUAL = [
    "insufficient_specs",
    "ambiguous_category",
    "brand_mismatch",
    "blurry_photo",
]
MOD_REASON_REJECT = [
    "prohibited_item",
    "spam_text",
    "counterfeit_risk",
    "restricted_wording",
]

CATEGORY_BY_ID: dict[int, str] = {
    1: "Смартфоны",
    2: "Ноутбуки",
    3: "Наушники",
    4: "Планшеты",
    5: "Мониторы",
    6: "Клавиатуры",
    7: "Игровые мыши",
    8: "Смарт-часы",
    9: "Кухонная техника",
    10: "Пылесосы",
    11: "Кофеварки",
    12: "Одежда",
    13: "Обувь",
    14: "Рюкзаки",
    15: "Товары для дома",
    16: "Посуда",
    17: "Косметика",
    18: "Детские товары",
    19: "Книги",
    20: "Спорттовары",
    21: "Автоаксессуары",
    22: "Зоотовары",
    23: "Садовая техника",
    24: "Инструменты",
}

CATEGORY_WEIGHTS = [
    8,
    7,
    6,
    4,
    5,
    3,
    4,
    3,
    5,
    4,
    4,
    6,
    5,
    4,
    5,
    4,
    5,
    4,
    3,
    4,
    3,
    3,
    3,
    3,
]

CATEGORY_PRICE_BANDS: dict[int, tuple[int, int]] = {
    1: (12000, 110000),
    2: (35000, 250000),
    3: (1500, 30000),
    4: (10000, 80000),
    5: (9000, 140000),
    6: (900, 18000),
    7: (700, 14000),
    8: (2500, 60000),
    9: (2000, 50000),
    10: (5000, 70000),
    11: (2500, 45000),
    12: (1200, 28000),
    13: (1500, 32000),
    14: (1000, 16000),
    15: (500, 22000),
    16: (400, 15000),
    17: (300, 8000),
    18: (300, 20000),
    19: (200, 3500),
    20: (800, 45000),
    21: (400, 15000),
    22: (200, 12000),
    23: (3000, 120000),
    24: (2000, 90000),
}

BRANDS = [
    "Aster",
    "Volna",
    "NordLine",
    "PrimeTech",
    "Orion",
    "Lumen",
    "Vertex",
    "Neonix",
    "Rivex",
    "MobiPro",
    "HomeArt",
    "Crafto",
    "UrbanFit",
    "Terra",
    "Foxly",
    "CleverBee",
    "AquaLeaf",
    "TrueSound",
    "PixelWay",
    "Smarton",
    "Brisk",
    "Optima",
    "Lira",
    "Futura",
    "SilverBox",
]

TITLE_ADJ = [
    "компактный",
    "универсальный",
    "премиальный",
    "лёгкий",
    "надежный",
    "эргономичный",
    "современный",
    "практичный",
]

COLOR_VALUES = ["черный", "белый", "серый", "синий", "зеленый", "красный", "бежевый"]
MATERIAL_VALUES = ["пластик", "металл", "текстиль", "керамика", "комбинированный"]
SIZE_VALUES = ["XS", "S", "M", "L", "XL", "универсальный"]

JSON_COLUMNS = {
    "ai_events": {"payload"},
    "user_features": {"category_counts", "brand_counts", "last_k_items"},
    "moderation_requests": {"attributes"},
    "training_jobs": {"params"},
    "model_registry": {"metrics"},
}

TABLE_COLUMNS: dict[str, list[str]] = {
    "ai_events": [
        "event_id",
        "event_type",
        "user_id",
        "item_id",
        "order_id",
        "session_id",
        "ts",
        "payload",
    ],
    "user_features": [
        "user_id",
        "updated_at",
        "category_counts",
        "brand_counts",
        "avg_check",
        "last_k_items",
        "last_active_ts",
    ],
    "item_features": [
        "item_id",
        "updated_at",
        "category_id",
        "price",
        "discount",
        "seller_id",
        "rating",
        "is_available",
    ],
    "rec_requests": [
        "request_id",
        "user_id",
        "context",
        "category_id",
        "item_id",
        "ts",
        "model_version",
        "latency_ms",
    ],
    "rec_results": [
        "request_id",
        "position",
        "item_id",
        "score",
        "reason_code",
    ],
    "rec_feedback": [
        "feedback_id",
        "request_id",
        "user_id",
        "item_id",
        "action",
        "ts",
    ],
    "moderation_requests": [
        "mod_request_id",
        "item_id",
        "seller_id",
        "title",
        "description",
        "category_id",
        "attributes",
        "ts",
        "model_version",
    ],
    "moderation_decisions": [
        "mod_request_id",
        "decision",
        "confidence",
        "reason_code",
        "decided_at",
    ],
    "training_jobs": [
        "job_id",
        "job_type",
        "status",
        "created_at",
        "started_at",
        "finished_at",
        "params",
        "error_message",
    ],
    "model_registry": [
        "model_version",
        "model_type",
        "created_at",
        "trained_job_id",
        "metrics",
        "artifact_uri",
        "is_active",
    ],
}


def fmt_ts(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def parse_ts(raw: str) -> datetime:
    return datetime.fromisoformat(raw)


def rand_ts(rng: random.Random, start: datetime, end: datetime) -> datetime:
    delta = int((end - start).total_seconds())
    return start + timedelta(seconds=rng.randint(0, delta))


def as_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def num2(value: float) -> str:
    return f"{value:.2f}"


def num4(value: float) -> str:
    return f"{value:.4f}"


def num6(value: float) -> str:
    return f"{value:.6f}"


def build_user_features(
    rng: random.Random,
    start_dt: datetime,
    now_dt: datetime,
    item_ids: list[int],
) -> tuple[list[dict[str, Any]], dict[int, list[int]]]:
    rows: list[dict[str, Any]] = []
    user_pref_categories: dict[int, list[int]] = {}
    category_ids = list(CATEGORY_BY_ID.keys())

    for user_id in range(1, N_USERS + 1):
        updated_at = rand_ts(rng, start_dt, now_dt)

        top_k = rng.randint(3, 7)
        pref_categories = rng.sample(category_ids, k=top_k)
        user_pref_categories[user_id] = pref_categories

        category_counts = {str(cat): rng.randint(4, 160) for cat in pref_categories}
        brand_counts = {rng.choice(BRANDS): rng.randint(2, 120) for _ in range(rng.randint(3, 6))}

        avg_check = None
        if rng.random() > 0.18:
            avg_check = num2(rng.uniform(900, 62000))

        last_items = rng.sample(item_ids, k=rng.randint(5, 12))

        last_active_ts = None
        if rng.random() > 0.06:
            low = max(start_dt, updated_at - timedelta(days=7))
            last_active_ts = fmt_ts(rand_ts(rng, low, now_dt))

        rows.append(
            {
                "user_id": user_id,
                "updated_at": fmt_ts(updated_at),
                "category_counts": as_json(category_counts),
                "brand_counts": as_json(brand_counts),
                "avg_check": avg_check,
                "last_k_items": as_json(last_items),
                "last_active_ts": last_active_ts,
            }
        )

    return rows, user_pref_categories


def build_item_features(
    rng: random.Random,
    start_dt: datetime,
    now_dt: datetime,
) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]], dict[int, list[int]], dict[int, list[int]], list[int], list[int]]:
    rows: list[dict[str, Any]] = []
    item_meta: dict[int, dict[str, Any]] = {}
    by_category: dict[int, list[int]] = defaultdict(list)
    available_by_category: dict[int, list[int]] = defaultdict(list)
    all_ids: list[int] = []
    available_ids: list[int] = []

    category_ids = list(CATEGORY_BY_ID.keys())

    for item_id in range(1, N_ITEMS + 1):
        category_id = rng.choices(category_ids, weights=CATEGORY_WEIGHTS, k=1)[0]
        low, high = CATEGORY_PRICE_BANDS[category_id]

        price = round(rng.uniform(low, high), 2)
        discount = 0.0
        if rng.random() < 0.34:
            discount = round(rng.uniform(3.0, 45.0), 2)

        seller_id = rng.randint(1, 260)
        rating = None if rng.random() < 0.08 else round(rng.uniform(3.2, 5.0), 2)
        is_available = rng.random() < 0.86

        updated_at = rand_ts(rng, start_dt, now_dt)

        row = {
            "item_id": item_id,
            "updated_at": fmt_ts(updated_at),
            "category_id": category_id,
            "price": num2(price),
            "discount": num2(discount),
            "seller_id": seller_id,
            "rating": None if rating is None else num2(rating),
            "is_available": is_available,
        }
        rows.append(row)

        meta = {
            "category_id": category_id,
            "price": price,
            "discount": discount,
            "seller_id": seller_id,
            "rating": rating,
            "is_available": is_available,
        }
        item_meta[item_id] = meta
        by_category[category_id].append(item_id)

        all_ids.append(item_id)
        if is_available:
            available_by_category[category_id].append(item_id)
            available_ids.append(item_id)

    return rows, item_meta, by_category, available_by_category, all_ids, available_ids


def build_training_jobs(
    rng: random.Random,
    start_dt: datetime,
    now_dt: datetime,
) -> tuple[list[dict[str, Any]], dict[str, list[int]]]:
    rows: list[dict[str, Any]] = []
    succeeded_ids: dict[str, list[int]] = {"recs_ranking": [], "moderation": []}

    for job_id in range(1, N_TRAINING_JOBS + 1):
        job_type = rng.choices(["recs_ranking", "moderation"], weights=[0.66, 0.34], k=1)[0]
        status = rng.choices(
            ["succeeded", "failed", "running", "queued", "canceled"],
            weights=[62, 12, 10, 10, 6],
            k=1,
        )[0]

        created_at = rand_ts(rng, start_dt, now_dt)
        started_at: datetime | None = None
        finished_at: datetime | None = None

        if status in {"running", "succeeded", "failed", "canceled"}:
            started_at = created_at + timedelta(minutes=rng.randint(1, 180))
            if started_at > now_dt:
                started_at = now_dt - timedelta(minutes=rng.randint(1, 30))

        if status in {"succeeded", "failed", "canceled"}:
            assert started_at is not None
            finished_at = started_at + timedelta(minutes=rng.randint(15, 900))
            if finished_at > now_dt:
                finished_at = now_dt - timedelta(minutes=rng.randint(1, 10))

        if job_type == "recs_ranking":
            params = {
                "window_days": 90,
                "embedding_dim": rng.choice([32, 64, 128]),
                "learning_rate": round(rng.uniform(0.0005, 0.02), 5),
                "negative_sampling": rng.choice(["uniform", "inbatch"]),
            }
        else:
            params = {
                "window_days": 120,
                "text_model": rng.choice(["tfidf_lr", "distilbert"]),
                "threshold": round(rng.uniform(0.55, 0.86), 3),
                "max_seq_len": rng.choice([128, 256, 384]),
            }

        error_message = None
        if status == "failed":
            error_message = rng.choice(
                [
                    "Не удалось загрузить батч признаков",
                    "Достигнут таймаут обучения",
                    "Ошибка валидации метрик",
                    "Недостаточно данных для сплита",
                ]
            )

        row = {
            "job_id": job_id,
            "job_type": job_type,
            "status": status,
            "created_at": fmt_ts(created_at),
            "started_at": fmt_ts(started_at) if started_at else None,
            "finished_at": fmt_ts(finished_at) if finished_at else None,
            "params": as_json(params),
            "error_message": error_message,
        }
        rows.append(row)

        if status == "succeeded":
            succeeded_ids[job_type].append(job_id)

    return rows, succeeded_ids


def build_model_registry(
    rng: random.Random,
    start_dt: datetime,
    now_dt: datetime,
    succeeded_ids: dict[str, list[int]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def _model_rows(model_type: str, n: int) -> list[dict[str, Any]]:
        local_rows: list[dict[str, Any]] = []
        for idx in range(1, n + 1):
            if model_type == "recs_ranking":
                version = f"recs_rank_v{idx}"
                metrics = {
                    "ndcg@10": round(rng.uniform(0.24, 0.52), 4),
                    "map@10": round(rng.uniform(0.16, 0.39), 4),
                    "coverage": round(rng.uniform(0.40, 0.86), 4),
                }
            else:
                version = f"moderation_v{idx}"
                metrics = {
                    "f1": round(rng.uniform(0.75, 0.95), 4),
                    "precision": round(rng.uniform(0.74, 0.96), 4),
                    "recall": round(rng.uniform(0.70, 0.93), 4),
                }

            trained_job_id = None
            candidates = succeeded_ids.get(model_type) or []
            if candidates and rng.random() > 0.15:
                trained_job_id = rng.choice(candidates)

            created_at = rand_ts(rng, start_dt, now_dt)
            local_rows.append(
                {
                    "model_version": version,
                    "model_type": model_type,
                    "created_at": fmt_ts(created_at),
                    "trained_job_id": trained_job_id,
                    "metrics": as_json(metrics),
                    "artifact_uri": f"s3://mini-ozon-models/{model_type}/{version}.bin",
                    "is_active": False,
                }
            )
        return local_rows

    rec_rows = _model_rows("recs_ranking", N_MODELS_RECS)
    mod_rows = _model_rows("moderation", N_MODELS_MOD)

    def _activate_latest(local_rows: list[dict[str, Any]]) -> None:
        latest = max(local_rows, key=lambda r: parse_ts(r["created_at"]))
        latest["is_active"] = True

    _activate_latest(rec_rows)
    _activate_latest(mod_rows)

    rows.extend(rec_rows)
    rows.extend(mod_rows)
    return rows


def build_rec_requests(
    rng: random.Random,
    start_dt: datetime,
    now_dt: datetime,
    user_pref_categories: dict[int, list[int]],
    item_meta: dict[int, dict[str, Any]],
    available_ids: list[int],
    rec_model_versions: list[str],
    active_rec_version: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for request_id in range(1, N_REC_REQUESTS + 1):
        user_id = rng.randint(1, N_USERS)
        context = rng.choices(["catalog", "item", "cart"], weights=[60, 25, 15], k=1)[0]

        category_id: int | None = None
        item_id: int | None = None

        user_pref = user_pref_categories[user_id]
        if context == "catalog":
            if rng.random() < 0.84:
                category_id = rng.choice(user_pref)
        elif context == "item":
            item_id = rng.choice(available_ids)
            category_id = item_meta[item_id]["category_id"]
        else:  # cart
            if rng.random() < 0.7:
                category_id = rng.choice(user_pref)
            if rng.random() < 0.6:
                item_id = rng.choice(available_ids)

        ts = rand_ts(rng, start_dt, now_dt)

        if rng.random() < 0.62:
            model_version = active_rec_version
        else:
            model_version = rng.choice(rec_model_versions)

        latency = int(max(12, min(550, rng.gauss(74, 24))))

        rows.append(
            {
                "request_id": request_id,
                "user_id": user_id,
                "context": context,
                "category_id": category_id,
                "item_id": item_id,
                "ts": fmt_ts(ts),
                "model_version": model_version,
                "latency_ms": latency,
            }
        )

    return rows


def build_rec_results(
    rng: random.Random,
    rec_requests: list[dict[str, Any]],
    user_pref_categories: dict[int, list[int]],
    item_meta: dict[int, dict[str, Any]],
    by_category: dict[int, list[int]],
    available_by_category: dict[int, list[int]],
    available_ids: list[int],
) -> tuple[list[dict[str, Any]], dict[int, list[int]]]:
    rows: list[dict[str, Any]] = []
    request_to_items: dict[int, list[int]] = {}

    for req in rec_requests:
        req_id = req["request_id"]
        user_id = req["user_id"]
        request_item_id = req["item_id"]

        primary_cat: int
        if req["category_id"] is not None:
            primary_cat = int(req["category_id"])
        elif request_item_id is not None:
            primary_cat = int(item_meta[int(request_item_id)]["category_id"])
        else:
            primary_cat = rng.choice(user_pref_categories[user_id])

        primary_pool = list(available_by_category.get(primary_cat) or by_category.get(primary_cat) or [])
        fallback_pool = available_ids

        chosen: list[int] = []
        chosen_set: set[int] = set()

        while len(chosen) < RESULTS_PER_REQUEST:
            if rng.random() < 0.74 and primary_pool:
                candidate = rng.choice(primary_pool)
            else:
                candidate = rng.choice(fallback_pool)

            if request_item_id is not None and candidate == request_item_id:
                continue
            if candidate in chosen_set:
                continue

            chosen.append(candidate)
            chosen_set.add(candidate)

        scores = sorted((rng.uniform(0.07, 0.99) for _ in range(RESULTS_PER_REQUEST)), reverse=True)
        request_to_items[req_id] = chosen

        for pos in range(1, RESULTS_PER_REQUEST + 1):
            rows.append(
                {
                    "request_id": req_id,
                    "position": pos,
                    "item_id": chosen[pos - 1],
                    "score": num6(scores[pos - 1]),
                    "reason_code": rng.choices(
                        REASON_CODES,
                        weights=[35, 30, 12, 10, 13],
                        k=1,
                    )[0],
                }
            )

    return rows, request_to_items


def build_rec_feedback(
    rng: random.Random,
    now_dt: datetime,
    rec_requests_by_id: dict[int, dict[str, Any]],
    rec_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    total_shows = len(rec_results)
    click_count = int(total_shows * CLICK_RATIO_TARGET)
    dislike_count = int(total_shows * DISLIKE_RATIO_TARGET)
    skip_count = int(total_shows * SKIP_RATIO_TARGET)

    if click_count + dislike_count + skip_count > total_shows:
        raise ValueError("Feedback target counts exceed total shown results")

    indices = list(range(total_shows))
    rng.shuffle(indices)

    click_idx = set(indices[:click_count])
    dislike_idx = set(indices[click_count : click_count + dislike_count])
    skip_idx = set(indices[click_count + dislike_count : click_count + dislike_count + skip_count])

    rows: list[dict[str, Any]] = []
    feedback_id = 1

    for idx, rr in enumerate(rec_results):
        action: str | None = None
        if idx in click_idx:
            action = "click"
        elif idx in dislike_idx:
            action = "dislike"
        elif idx in skip_idx:
            action = "skip"

        if action is None:
            continue

        req = rec_requests_by_id[rr["request_id"]]
        base_ts = parse_ts(req["ts"])
        fb_ts = base_ts + timedelta(seconds=rng.randint(8, 32 * 3600))
        if fb_ts > now_dt:
            fb_ts = now_dt - timedelta(seconds=rng.randint(1, 300))

        rows.append(
            {
                "feedback_id": feedback_id,
                "request_id": rr["request_id"],
                "user_id": req["user_id"],
                "item_id": rr["item_id"],
                "action": action,
                "ts": fmt_ts(fb_ts),
            }
        )
        feedback_id += 1

    return rows


def build_moderation_tables(
    rng: random.Random,
    start_dt: datetime,
    now_dt: datetime,
    item_meta: dict[int, dict[str, Any]],
    moderation_versions: list[str],
    active_moderation_version: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    req_rows: list[dict[str, Any]] = []
    decision_rows: list[dict[str, Any]] = []

    item_ids = list(item_meta.keys())

    publish_n = int(N_MOD_REQUESTS * 0.80)
    manual_n = int(N_MOD_REQUESTS * 0.15)
    reject_n = N_MOD_REQUESTS - publish_n - manual_n

    decisions = ["publish"] * publish_n + ["manual_review"] * manual_n + ["reject"] * reject_n
    rng.shuffle(decisions)

    for mod_request_id in range(1, N_MOD_REQUESTS + 1):
        item_id = rng.choice(item_ids)
        meta = item_meta[item_id]
        category_id = int(meta["category_id"])
        seller_id = int(meta["seller_id"])
        category_name = CATEGORY_BY_ID[category_id]
        brand = rng.choice(BRANDS)

        title = f"{brand} {category_name.lower()} {rng.choice(TITLE_ADJ)}"
        description = (
            f"{category_name}: аккуратное исполнение, стабильная работа и удобное использование каждый день."
        )

        attributes = {
            "brand": brand,
            "color": rng.choice(COLOR_VALUES),
            "material": rng.choice(MATERIAL_VALUES),
            "size": rng.choice(SIZE_VALUES),
            "warranty_months": rng.choice([6, 12, 18, 24]),
        }

        ts = rand_ts(rng, start_dt, now_dt)
        model_version = active_moderation_version if rng.random() < 0.7 else rng.choice(moderation_versions)

        req_rows.append(
            {
                "mod_request_id": mod_request_id,
                "item_id": item_id,
                "seller_id": seller_id,
                "title": title,
                "description": description,
                "category_id": category_id,
                "attributes": as_json(attributes),
                "ts": fmt_ts(ts),
                "model_version": model_version,
            }
        )

        decision = decisions[mod_request_id - 1]
        if decision == "publish":
            confidence = rng.uniform(0.78, 0.995)
            reason_code = None if rng.random() < 0.78 else "ok"
        elif decision == "manual_review":
            confidence = rng.uniform(0.45, 0.79)
            reason_code = rng.choice(MOD_REASON_MANUAL)
        else:
            confidence = rng.uniform(0.70, 0.985)
            reason_code = rng.choice(MOD_REASON_REJECT)

        decided_at = ts + timedelta(minutes=rng.randint(3, 960))
        if decided_at > now_dt:
            decided_at = now_dt - timedelta(seconds=rng.randint(1, 120))

        decision_rows.append(
            {
                "mod_request_id": mod_request_id,
                "decision": decision,
                "confidence": num4(confidence),
                "reason_code": reason_code,
                "decided_at": fmt_ts(decided_at),
            }
        )

    return req_rows, decision_rows


def build_ai_events(
    rng: random.Random,
    start_dt: datetime,
    now_dt: datetime,
    rec_requests: list[dict[str, Any]],
    request_to_items: dict[int, list[int]],
    rec_feedback: list[dict[str, Any]],
    item_meta: dict[int, dict[str, Any]],
    available_ids: list[int],
) -> list[dict[str, Any]]:
    tmp_events: list[dict[str, Any]] = []

    def add_event(
        event_type: str,
        ts: datetime,
        user_id: int | None,
        item_id: int | None,
        order_id: int | None,
        session_id: str | None,
        payload: dict[str, Any],
    ) -> None:
        tmp_events.append(
            {
                "event_type": event_type,
                "user_id": user_id,
                "item_id": item_id,
                "order_id": order_id,
                "session_id": session_id,
                "ts": ts,
                "payload": payload,
            }
        )

    # RecommendationShown events (one event per request)
    for req in rec_requests:
        req_ts = parse_ts(req["ts"])
        request_id = req["request_id"]
        rec_items = request_to_items[request_id]

        add_event(
            event_type="RecommendationShown",
            ts=req_ts,
            user_id=req["user_id"],
            item_id=req["item_id"],
            order_id=None,
            session_id=f"sess_{req['user_id']}_{rng.randint(1000, 9999)}",
            payload={
                "request_id": request_id,
                "context": req["context"],
                "items": rec_items,
                "model_version": req["model_version"],
            },
        )

    # CatalogViewed events
    for _ in range(N_CATALOG_VIEWS):
        user_id = rng.randint(1, N_USERS)
        item_id = rng.choice(available_ids)
        meta = item_meta[item_id]
        ts = rand_ts(rng, start_dt, now_dt)

        add_event(
            event_type="CatalogViewed",
            ts=ts,
            user_id=user_id,
            item_id=item_id,
            order_id=None,
            session_id=f"sess_{user_id}_{rng.randint(1000, 9999)}",
            payload={
                "category_id": meta["category_id"],
                "source": "catalog",
            },
        )

    # AddToCart events
    for _ in range(N_ADD_TO_CART):
        user_id = rng.randint(1, N_USERS)
        item_id = rng.choice(available_ids)
        meta = item_meta[item_id]
        ts = rand_ts(rng, start_dt, now_dt)

        add_event(
            event_type="AddToCart",
            ts=ts,
            user_id=user_id,
            item_id=item_id,
            order_id=None,
            session_id=f"sess_{user_id}_{rng.randint(1000, 9999)}",
            payload={
                "quantity": rng.randint(1, 3),
                "price": num2(meta["price"]),
            },
        )

    # OrderCreated / OrderPaid events
    order_events: list[tuple[int, int, datetime, list[dict[str, Any]], str]] = []
    base_order_id = 500_000
    for idx in range(N_ORDER_CREATED):
        order_id = base_order_id + idx
        user_id = rng.randint(1, N_USERS)
        ts = rand_ts(rng, start_dt, now_dt)

        item_count = rng.randint(1, 4)
        order_items: list[dict[str, Any]] = []
        total = 0.0
        for _ in range(item_count):
            item_id = rng.choice(available_ids)
            qty = rng.randint(1, 2)
            price = float(item_meta[item_id]["price"])
            total += price * qty
            order_items.append({"item_id": item_id, "qty": qty, "price": num2(price)})

        add_event(
            event_type="OrderCreated",
            ts=ts,
            user_id=user_id,
            item_id=None,
            order_id=order_id,
            session_id=None,
            payload={
                "items": order_items,
                "total": num2(total),
                "currency": "RUB",
            },
        )
        order_events.append((order_id, user_id, ts, order_items, num2(total)))

    paid_orders = rng.sample(order_events, k=N_ORDER_PAID)
    for order_id, user_id, created_ts, items, total in paid_orders:
        paid_ts = created_ts + timedelta(minutes=rng.randint(10, 1200))
        if paid_ts > now_dt:
            paid_ts = now_dt - timedelta(seconds=rng.randint(1, 120))
        add_event(
            event_type="OrderPaid",
            ts=paid_ts,
            user_id=user_id,
            item_id=None,
            order_id=order_id,
            session_id=None,
            payload={
                "items": items,
                "total": total,
                "payment_method": rng.choice(["card", "sbp", "wallet"]),
            },
        )

    # Click/dislike events derived from feedback
    for fb in rec_feedback:
        if fb["action"] == "click":
            event_type = "RecommendationClicked"
        elif fb["action"] == "dislike":
            event_type = "RecommendationDisliked"
        else:
            continue

        add_event(
            event_type=event_type,
            ts=parse_ts(fb["ts"]),
            user_id=fb["user_id"],
            item_id=fb["item_id"],
            order_id=None,
            session_id=f"sess_{fb['user_id']}_{rng.randint(1000, 9999)}",
            payload={
                "request_id": fb["request_id"],
                "action": fb["action"],
            },
        )

    # Sort by timestamp and assign event_id
    tmp_events.sort(key=lambda e: e["ts"])

    rows: list[dict[str, Any]] = []
    for event_id, event in enumerate(tmp_events, start=1):
        rows.append(
            {
                "event_id": event_id,
                "event_type": event["event_type"],
                "user_id": event["user_id"],
                "item_id": event["item_id"],
                "order_id": event["order_id"],
                "session_id": event["session_id"],
                "ts": fmt_ts(event["ts"]),
                "payload": as_json(event["payload"]),
            }
        )

    return rows


def validate_dataset(dataset: dict[str, list[dict[str, Any]]], start_dt: datetime, now_dt: datetime) -> None:
    def fail(msg: str) -> None:
        raise ValueError(msg)

    # Required minimum counts
    required = {
        "ai_events": 3000,
        "rec_requests": 1200,
        "rec_results": 1200 * 10,
        "rec_feedback": 800,
        "moderation_requests": 300,
        "moderation_decisions": 300,
        "user_features": 400,
        "item_features": 800,
        "training_jobs": 30,
        "model_registry": 10,
    }

    for table, min_count in required.items():
        actual = len(dataset[table])
        if actual < min_count:
            fail(f"{table}: expected >= {min_count}, got {actual}")

    if len(dataset["rec_results"]) != len(dataset["rec_requests"]) * RESULTS_PER_REQUEST:
        fail("rec_results count must equal rec_requests * 10")

    total_rows = sum(len(rows) for rows in dataset.values())
    if total_rows < 1000:
        fail(f"Total rows must be >= 1000, got {total_rows}")

    # Unique PK checks
    def ensure_unique(rows: list[dict[str, Any]], key_fn: Any, label: str) -> None:
        keys = [key_fn(r) for r in rows]
        if len(keys) != len(set(keys)):
            fail(f"Duplicate PK in {label}")

    ensure_unique(dataset["ai_events"], lambda r: r["event_id"], "ai_events")
    ensure_unique(dataset["user_features"], lambda r: r["user_id"], "user_features")
    ensure_unique(dataset["item_features"], lambda r: r["item_id"], "item_features")
    ensure_unique(dataset["rec_requests"], lambda r: r["request_id"], "rec_requests")
    ensure_unique(dataset["rec_results"], lambda r: (r["request_id"], r["position"]), "rec_results")
    ensure_unique(dataset["rec_feedback"], lambda r: r["feedback_id"], "rec_feedback")
    ensure_unique(dataset["moderation_requests"], lambda r: r["mod_request_id"], "moderation_requests")
    ensure_unique(dataset["moderation_decisions"], lambda r: r["mod_request_id"], "moderation_decisions")
    ensure_unique(dataset["training_jobs"], lambda r: r["job_id"], "training_jobs")
    ensure_unique(dataset["model_registry"], lambda r: r["model_version"], "model_registry")

    # Foreign keys
    req_ids = {r["request_id"] for r in dataset["rec_requests"]}
    mod_req_ids = {r["mod_request_id"] for r in dataset["moderation_requests"]}
    job_ids = {r["job_id"] for r in dataset["training_jobs"]}

    for row in dataset["rec_results"]:
        if row["request_id"] not in req_ids:
            fail("rec_results.request_id FK violation")
    for row in dataset["rec_feedback"]:
        if row["request_id"] not in req_ids:
            fail("rec_feedback.request_id FK violation")
    for row in dataset["moderation_decisions"]:
        if row["mod_request_id"] not in mod_req_ids:
            fail("moderation_decisions.mod_request_id FK violation")
    for row in dataset["model_registry"]:
        job_id = row["trained_job_id"]
        if job_id is not None and job_id not in job_ids:
            fail("model_registry.trained_job_id FK violation")

    # rec_feedback request/item should exist in shown results
    shown_pairs = {(r["request_id"], r["item_id"]) for r in dataset["rec_results"]}
    for row in dataset["rec_feedback"]:
        if (row["request_id"], row["item_id"]) not in shown_pairs:
            fail("rec_feedback item not present in rec_results for request")

    # Date range checks
    def check_ts(raw: str, label: str) -> None:
        dt = parse_ts(raw)
        if dt < start_dt or dt > now_dt:
            fail(f"{label} out of 90-day range: {raw}")

    for row in dataset["ai_events"]:
        check_ts(row["ts"], "ai_events.ts")
    for row in dataset["user_features"]:
        check_ts(row["updated_at"], "user_features.updated_at")
        if row["last_active_ts"]:
            check_ts(row["last_active_ts"], "user_features.last_active_ts")
    for row in dataset["item_features"]:
        check_ts(row["updated_at"], "item_features.updated_at")
    for row in dataset["rec_requests"]:
        check_ts(row["ts"], "rec_requests.ts")
    for row in dataset["rec_feedback"]:
        check_ts(row["ts"], "rec_feedback.ts")
    for row in dataset["moderation_requests"]:
        check_ts(row["ts"], "moderation_requests.ts")
    for row in dataset["moderation_decisions"]:
        check_ts(row["decided_at"], "moderation_decisions.decided_at")
    for row in dataset["training_jobs"]:
        check_ts(row["created_at"], "training_jobs.created_at")
        if row["started_at"]:
            check_ts(row["started_at"], "training_jobs.started_at")
        if row["finished_at"]:
            check_ts(row["finished_at"], "training_jobs.finished_at")
    for row in dataset["model_registry"]:
        check_ts(row["created_at"], "model_registry.created_at")

    # Domain checks
    if any(r["context"] not in CONTEXT_VALUES for r in dataset["rec_requests"]):
        fail("rec_requests.context contains invalid value")

    if any(r["status"] not in TRAINING_STATUS_VALUES for r in dataset["training_jobs"]):
        fail("training_jobs.status contains invalid value")

    if any(r["model_type"] not in MODEL_TYPE_VALUES for r in dataset["model_registry"]):
        fail("model_registry.model_type contains invalid value")

    # Active models: exactly one per type
    active_by_type: dict[str, int] = defaultdict(int)
    for row in dataset["model_registry"]:
        if row["is_active"]:
            active_by_type[row["model_type"]] += 1
    for model_type in MODEL_TYPE_VALUES:
        if active_by_type.get(model_type, 0) != 1:
            fail(f"model_registry.is_active must have exactly one true for {model_type}")

    # Distribution checks
    event_counts = Counter(row["event_type"] for row in dataset["ai_events"])
    if event_counts["CatalogViewed"] <= event_counts["OrderPaid"]:
        fail("CatalogViewed must be more frequent than OrderPaid")
    if event_counts["RecommendationShown"] <= event_counts["OrderPaid"]:
        fail("RecommendationShown must be more frequent than OrderPaid")

    total_shows = len(dataset["rec_results"])
    action_counts = Counter(row["action"] for row in dataset["rec_feedback"])
    click_ratio = action_counts["click"] / total_shows
    dislike_ratio = action_counts["dislike"] / total_shows

    if not (0.15 <= click_ratio <= 0.25):
        fail(f"click ratio out of range: {click_ratio:.4f}")
    if not (0.02 <= dislike_ratio <= 0.05):
        fail(f"dislike ratio out of range: {dislike_ratio:.4f}")

    decision_counts = Counter(row["decision"] for row in dataset["moderation_decisions"])
    total_mod = len(dataset["moderation_decisions"])
    publish_ratio = decision_counts["publish"] / total_mod
    manual_ratio = decision_counts["manual_review"] / total_mod
    reject_ratio = decision_counts["reject"] / total_mod

    if not (0.75 <= publish_ratio <= 0.85):
        fail(f"publish ratio out of range: {publish_ratio:.4f}")
    if not (0.10 <= manual_ratio <= 0.20):
        fail(f"manual_review ratio out of range: {manual_ratio:.4f}")
    if not (0.03 <= reject_ratio <= 0.10):
        fail(f"reject ratio out of range: {reject_ratio:.4f}")


def normalize_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def write_table_csv(path: Path, table_name: str, rows: list[dict[str, Any]]) -> None:
    columns = TABLE_COLUMNS[table_name]
    json_columns = JSON_COLUMNS.get(table_name, set())

    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, delimiter=",")
        writer.writeheader()

        for row in rows:
            out_row: dict[str, str] = {}
            for col in columns:
                value = row.get(col)
                if col in json_columns and value is not None:
                    # Value may already be JSON string; if not, serialize.
                    if isinstance(value, str):
                        out_row[col] = value
                    else:
                        out_row[col] = as_json(value)
                else:
                    out_row[col] = normalize_cell(value)
            writer.writerow(out_row)


def write_load_sql(out_dir: Path) -> None:
    load_order = [
        "training_jobs",
        "model_registry",
        "user_features",
        "item_features",
        "rec_requests",
        "rec_results",
        "rec_feedback",
        "moderation_requests",
        "moderation_decisions",
        "ai_events",
    ]

    lines: list[str] = []
    lines.append("-- Generated load script for PostgreSQL")
    lines.append("-- Run from project root, then: psql -d <db> -f out/load.sql")
    lines.append("BEGIN;")
    lines.append("")

    for table in load_order:
        cols = ", ".join(TABLE_COLUMNS[table])
        lines.append(
            f"COPY {table} ({cols}) FROM './out/{table}.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');"
        )

    lines.append("")
    lines.append("COMMIT;")
    lines.append("")

    (out_dir / "load.sql").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rng = random.Random(SEED)

    now_dt = datetime.now(timezone.utc)
    start_dt = now_dt - timedelta(days=90)

    item_features, item_meta, by_category, available_by_category, item_ids, available_ids = build_item_features(
        rng,
        start_dt,
        now_dt,
    )

    user_features, user_pref_categories = build_user_features(
        rng,
        start_dt,
        now_dt,
        item_ids,
    )

    training_jobs, succeeded_ids = build_training_jobs(rng, start_dt, now_dt)

    model_registry = build_model_registry(rng, start_dt, now_dt, succeeded_ids)
    rec_model_versions = [r["model_version"] for r in model_registry if r["model_type"] == "recs_ranking"]
    mod_model_versions = [r["model_version"] for r in model_registry if r["model_type"] == "moderation"]
    active_rec_version = next(r["model_version"] for r in model_registry if r["model_type"] == "recs_ranking" and r["is_active"])
    active_mod_version = next(r["model_version"] for r in model_registry if r["model_type"] == "moderation" and r["is_active"])

    rec_requests = build_rec_requests(
        rng,
        start_dt,
        now_dt,
        user_pref_categories,
        item_meta,
        available_ids,
        rec_model_versions,
        active_rec_version,
    )

    rec_results, request_to_items = build_rec_results(
        rng,
        rec_requests,
        user_pref_categories,
        item_meta,
        by_category,
        available_by_category,
        available_ids,
    )

    rec_requests_by_id = {r["request_id"]: r for r in rec_requests}
    rec_feedback = build_rec_feedback(rng, now_dt, rec_requests_by_id, rec_results)

    moderation_requests, moderation_decisions = build_moderation_tables(
        rng,
        start_dt,
        now_dt,
        item_meta,
        mod_model_versions,
        active_mod_version,
    )

    ai_events = build_ai_events(
        rng,
        start_dt,
        now_dt,
        rec_requests,
        request_to_items,
        rec_feedback,
        item_meta,
        available_ids,
    )

    dataset: dict[str, list[dict[str, Any]]] = {
        "ai_events": ai_events,
        "user_features": user_features,
        "item_features": item_features,
        "rec_requests": rec_requests,
        "rec_results": rec_results,
        "rec_feedback": rec_feedback,
        "moderation_requests": moderation_requests,
        "moderation_decisions": moderation_decisions,
        "training_jobs": training_jobs,
        "model_registry": model_registry,
    }

    validate_dataset(dataset, start_dt, now_dt)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for table_name, rows in dataset.items():
        write_table_csv(OUT_DIR / f"{table_name}.csv", table_name, rows)

    write_load_sql(OUT_DIR)

    # Short report
    print("Generated CSV files in ./out")
    for table_name in [
        "ai_events",
        "rec_requests",
        "rec_results",
        "rec_feedback",
        "moderation_requests",
        "moderation_decisions",
        "user_features",
        "item_features",
        "training_jobs",
        "model_registry",
    ]:
        print(f"{table_name}: {len(dataset[table_name])}")

    event_counts = Counter(r["event_type"] for r in dataset["ai_events"])
    action_counts = Counter(r["action"] for r in dataset["rec_feedback"])
    decision_counts = Counter(r["decision"] for r in dataset["moderation_decisions"])

    total_shows = len(dataset["rec_results"])
    print(f"click_ratio_from_shows: {action_counts['click'] / total_shows:.4f}")
    print(f"dislike_ratio_from_shows: {action_counts['dislike'] / total_shows:.4f}")
    print(
        "moderation_ratios: "
        f"publish={decision_counts['publish'] / len(dataset['moderation_decisions']):.4f}, "
        f"manual_review={decision_counts['manual_review'] / len(dataset['moderation_decisions']):.4f}, "
        f"reject={decision_counts['reject'] / len(dataset['moderation_decisions']):.4f}"
    )
    print(
        "ai_event_frequency: "
        f"CatalogViewed={event_counts['CatalogViewed']}, "
        f"RecommendationShown={event_counts['RecommendationShown']}, "
        f"OrderPaid={event_counts['OrderPaid']}"
    )


if __name__ == "__main__":
    main()
