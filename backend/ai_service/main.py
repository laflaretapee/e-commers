import re
import time
import math
import random
from datetime import datetime, timedelta
from typing import Any, Literal

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import AsyncSessionLocal, Base, engine, get_db
from .models import ItemFeature, RecFeedback, RecRequest, RecResult
from .repositories import (
    EventRepository,
    FeatureRepository,
    ModelRegistryRepository,
    ModerationRepository,
    RecLogRepository,
    TrainingJobRepository,
)
from .schemas import (
    AIEventCreate,
    AIEventOut,
    ItemFeatureUpsert,
    ModelOut,
    ModelRegisterCreate,
    ModerationAppealCreate,
    ModerationAppealResultCreate,
    ModerationCheckRequest,
    ModerationDecisionOut,
    RecommendationFeedbackCreate,
    RecommendationItem,
    RecommendationTrainingRunRequest,
    RecommendationTrainingRunResponse,
    RecommendationRequest,
    RecommendationResponse,
    TrainingJobCreate,
    TrainingJobOut,
    TrainingJobUpdate,
)

app = FastAPI(
    title="AI Service",
    description="Event Store, Feature Store, moderation and recommendation API.",
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

FEEDBACK_EVENT_MAP = {
    "clicked": "RecommendationClicked",
    "skipped": "RecommendationSkipped",
    "disliked": "RecommendationDisliked",
}

BANNED_PATTERNS = [
    (re.compile(r"(наркот|оружи|casino|ставк|adult|порно)", re.IGNORECASE), "prohibited_content"),
    (re.compile(r"https?://|www\.", re.IGNORECASE), "external_link_detected"),
    (re.compile(r"\+?\d[\d\-\(\)\s]{7,}\d"), "contact_info_detected"),
]

INTERACTION_WEIGHTS = {
    "CatalogViewed": 1.0,
    "AddToCart": 2.0,
    "OrderCreated": 4.0,
    "RecommendationClicked": 1.5,
}

DEFAULT_RANKING_WEIGHTS = {
    "bias": 0.0,
    "purchase_count": 3.0,
    "add_to_cart_count": 1.6,
    "view_count": 0.25,
    "positive_feedback": 2.0,
    "negative_feedback": -0.8,
}

DEFAULT_CONTEXT_WEIGHTS = {
    "requested_category_bonus": 2.5,
    "user_preference_multiplier": 1.3,
    "cart_match_multiplier": 1.8,
}


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_log1p(value: Any) -> float:
    return math.log1p(max(0.0, _to_float(value, 0.0)))


def _sigmoid(value: float) -> float:
    if value >= 0:
        exp_val = math.exp(-value)
        return 1.0 / (1.0 + exp_val)
    exp_val = math.exp(value)
    return exp_val / (1.0 + exp_val)


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _resolve_weight(model_metrics: dict[str, Any] | None, section: str, key: str, default: float) -> float:
    if not model_metrics:
        return default
    raw_section = model_metrics.get(section)
    if not isinstance(raw_section, dict):
        return default
    return _to_float(raw_section.get(key), default=default)


def _item_feature_vector(item_features: dict[str, Any]) -> list[float]:
    return [
        1.0,
        _safe_log1p(item_features.get("purchase_count")),
        _safe_log1p(item_features.get("add_to_cart_count")),
        _safe_log1p(item_features.get("view_count")),
        _safe_log1p(item_features.get("positive_feedback")),
        _safe_log1p(item_features.get("negative_feedback")),
    ]


def _to_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


async def _bootstrap_default_models() -> None:
    async with AsyncSessionLocal() as db:
        repo = ModelRegistryRepository(db)
        rec_model = await repo.get_active_model("recommendation")
        mod_model = await repo.get_active_model("moderation")

        if rec_model is None:
            await repo.register_model(
                model_type="recommendation",
                model_version="heuristic-v1",
                metrics={"source": "rule-based"},
                artifact_uri="inline://heuristic-v1",
                is_active=True,
            )
        if mod_model is None:
            await repo.register_model(
                model_type="moderation",
                model_version="rule-based-v1",
                metrics={"source": "rule-based"},
                artifact_uri="inline://rule-based-v1",
                is_active=True,
            )

        await db.commit()


async def _update_user_profile(
    feature_repo: FeatureRepository,
    user_id: int,
    event_type: str,
    category_id: int | None,
    weight: float,
) -> None:
    existing = await feature_repo.get_user_features(user_id)
    data = dict(existing.features or {}) if existing else {}

    event_counts = dict(data.get("event_counts") or {})
    event_counts[event_type] = int(event_counts.get(event_type, 0)) + 1
    data["event_counts"] = event_counts

    if category_id is not None:
        category_scores = dict(data.get("category_scores") or {})
        key = str(category_id)
        category_scores[key] = float(category_scores.get(key, 0.0)) + weight
        data["category_scores"] = category_scores

    data["last_event_at"] = datetime.utcnow().isoformat()
    await feature_repo.upsert_user_features(user_id=user_id, features_patch=data)


async def _increment_item_counter(
    feature_repo: FeatureRepository,
    item_id: int,
    counter_key: str,
    delta: float = 1.0,
    category_id: int | None = None,
    price: float | None = None,
    stock: int | None = None,
) -> None:
    existing = await feature_repo.get_item_features(item_id)
    data = dict(existing.features or {}) if existing else {}
    data[counter_key] = float(data.get(counter_key, 0.0)) + delta
    await feature_repo.upsert_item_features(
        item_id=item_id,
        category_id=category_id,
        price=price,
        stock=stock,
        features_patch=data,
    )


async def _apply_event_to_features(event: AIEventCreate, feature_repo: FeatureRepository) -> None:
    payload = event.payload or {}
    category_id = _to_int(payload.get("category_id"))
    price = payload.get("price")
    stock = _to_int(payload.get("stock"))

    weight = INTERACTION_WEIGHTS.get(event.event_type)
    if event.user_id and weight is not None:
        await _update_user_profile(feature_repo, event.user_id, event.event_type, category_id, weight)

    if event.event_type == "CatalogViewed" and event.item_id:
        await _increment_item_counter(feature_repo, event.item_id, "view_count", category_id=category_id, price=price, stock=stock)
    elif event.event_type == "AddToCart" and event.item_id:
        quantity = max(1, _to_int(payload.get("quantity")) or 1)
        await _increment_item_counter(
            feature_repo,
            event.item_id,
            "add_to_cart_count",
            delta=float(quantity),
            category_id=category_id,
            price=price,
            stock=stock,
        )
    elif event.event_type == "RemoveFromCart" and event.item_id:
        quantity = max(1, _to_int(payload.get("quantity")) or 1)
        await _increment_item_counter(
            feature_repo,
            event.item_id,
            "remove_from_cart_count",
            delta=float(quantity),
            category_id=category_id,
            price=price,
            stock=stock,
        )
    elif event.event_type == "OrderCreated":
        items = payload.get("items") or []
        for item in items:
            item_id = _to_int(item.get("item_id") or item.get("product_id"))
            if not item_id:
                continue
            qty = max(1, _to_int(item.get("quantity")) or 1)
            item_price = item.get("price")
            item_category_id = _to_int(item.get("category_id")) or category_id
            await _increment_item_counter(
                feature_repo,
                item_id=item_id,
                counter_key="purchase_count",
                delta=float(qty),
                category_id=item_category_id,
                price=item_price,
            )
            if event.user_id:
                await _update_user_profile(
                    feature_repo,
                    event.user_id,
                    event.event_type,
                    item_category_id,
                    INTERACTION_WEIGHTS["OrderCreated"] * qty,
                )
    elif event.event_type in {"CatalogItemCreated", "CatalogItemUpdated"} and event.item_id:
        await feature_repo.upsert_item_features(
            item_id=event.item_id,
            category_id=category_id,
            price=price,
            stock=stock,
            features_patch={"last_catalog_sync_at": datetime.utcnow().isoformat()},
        )
    elif event.event_type == "CatalogItemDeleted" and event.item_id:
        await feature_repo.upsert_item_features(
            item_id=event.item_id,
            stock=0,
            features_patch={"is_deleted": True},
        )


def _score_item(
    item_features: dict[str, Any],
    preferred_categories: dict[int, float],
    cart_categories: dict[int, float],
    category_id: int | None,
    context: str,
    item_category_id: int | None,
    ranking_weights: dict[str, float],
    context_weights: dict[str, float],
) -> tuple[float, str]:
    item_vector = _item_feature_vector(item_features)
    score = _dot(
        item_vector,
        [
            ranking_weights["bias"],
            ranking_weights["purchase_count"],
            ranking_weights["add_to_cart_count"],
            ranking_weights["view_count"],
            ranking_weights["positive_feedback"],
            ranking_weights["negative_feedback"],
        ],
    )
    reason = "popularity"

    if category_id is not None and item_category_id == category_id:
        score += context_weights["requested_category_bonus"]
        reason = "requested_category"

    if item_category_id in preferred_categories:
        score += preferred_categories[item_category_id] * context_weights["user_preference_multiplier"]
        reason = "user_preference"

    if context == "cart" and item_category_id in cart_categories:
        score += cart_categories[item_category_id] * context_weights["cart_match_multiplier"]
        reason = "cart_match"

    return score, reason


async def _generate_recommendations(
    request: RecommendationRequest,
    feature_repo: FeatureRepository,
    model_metrics: dict[str, Any] | None = None,
) -> list[RecommendationItem]:
    excluded = set(request.item_ids or [])
    if request.item_id is not None:
        excluded.add(request.item_id)

    preferred_categories: dict[int, float] = {}
    user_features = await feature_repo.get_user_features(request.user_id)
    if user_features and isinstance(user_features.features, dict):
        raw_scores = user_features.features.get("category_scores") or {}
        for key, value in raw_scores.items():
            key_int = _to_int(key)
            if key_int is not None:
                preferred_categories[key_int] = float(value)

    cart_categories: dict[int, float] = {}
    if request.item_ids:
        cart_items = await feature_repo.get_item_features_by_ids(request.item_ids)
        for item in cart_items:
            if item.category_id is None:
                continue
            cart_categories[item.category_id] = cart_categories.get(item.category_id, 0.0) + 1.0

    ranking_weights = {
        key: _resolve_weight(model_metrics, "ranking_weights", key, default)
        for key, default in DEFAULT_RANKING_WEIGHTS.items()
    }
    context_weights = {
        key: _resolve_weight(model_metrics, "context_weights", key, default)
        for key, default in DEFAULT_CONTEXT_WEIGHTS.items()
    }

    candidates = []
    seen_ids: set[int] = set()

    async def append_candidates(category: int | None, limit: int) -> None:
        rows = await feature_repo.list_item_features(
            category_id=category,
            exclude_item_ids=excluded,
            limit=limit,
        )
        for row in rows:
            if row.item_id in seen_ids:
                continue
            seen_ids.add(row.item_id)
            candidates.append(row)

    if request.category_id is not None:
        await append_candidates(request.category_id, 300)
        if not candidates:
            await append_candidates(None, 300)
    else:
        for category, _ in sorted(cart_categories.items(), key=lambda it: it[1], reverse=True)[:3]:
            await append_candidates(category, 120)
        if not candidates:
            for category, _ in sorted(preferred_categories.items(), key=lambda it: it[1], reverse=True)[:3]:
                await append_candidates(category, 120)
        if not candidates:
            await append_candidates(None, 300)

    scored: list[RecommendationItem] = []
    for row in candidates:
        if row.stock is not None and row.stock <= 0:
            continue
        score, reason = _score_item(
            item_features=dict(row.features or {}),
            preferred_categories=preferred_categories,
            cart_categories=cart_categories,
            category_id=request.category_id,
            context=request.context,
            item_category_id=row.category_id,
            ranking_weights=ranking_weights,
            context_weights=context_weights,
        )
        if score <= 0:
            score = 0.1
        scored.append(
            RecommendationItem(
                item_id=row.item_id,
                score=round(score, 4),
                reason=reason,
            )
        )

    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[: request.limit]


def _target_from_feedback(action: str | None) -> tuple[float, float]:
    if action == "clicked":
        return 1.0, 1.0
    if action == "disliked":
        return 0.0, 1.0
    if action == "skipped":
        return 0.0, 0.7
    return 0.0, 0.15


async def _load_recommendation_training_samples(
    db: AsyncSession,
    lookback_days: int,
    max_samples: int,
) -> tuple[list[tuple[list[float], float, float]], dict[str, Any]]:
    cutoff = datetime.utcnow() - timedelta(days=lookback_days)
    samples_stmt = (
        select(RecResult.request_id, RecResult.item_id)
        .join(RecRequest, RecResult.request_id == RecRequest.request_id)
        .where(RecRequest.ts >= cutoff)
        .order_by(desc(RecRequest.ts))
        .limit(max_samples)
    )
    sample_rows = list((await db.execute(samples_stmt)).all())
    if not sample_rows:
        return [], {
            "sample_count": 0,
            "positive_samples": 0,
            "feedback_rows": 0,
            "items_with_features": 0,
            "lookback_days": lookback_days,
        }

    request_ids = {int(row[0]) for row in sample_rows}
    item_ids = {int(row[1]) for row in sample_rows}

    feedback_stmt = select(RecFeedback.request_id, RecFeedback.item_id, RecFeedback.action, RecFeedback.ts).where(
        RecFeedback.request_id.in_(request_ids)
    )
    feedback_rows = list((await db.execute(feedback_stmt)).all())
    latest_feedback: dict[tuple[int, int], tuple[str, datetime | None]] = {}
    for request_id, item_id, action, ts in feedback_rows:
        key = (int(request_id), int(item_id))
        previous = latest_feedback.get(key)
        if previous is None or (previous[1] or datetime.min) <= (ts or datetime.min):
            latest_feedback[key] = (str(action), ts)

    feature_stmt = select(ItemFeature.item_id, ItemFeature.features).where(ItemFeature.item_id.in_(item_ids))
    feature_rows = list((await db.execute(feature_stmt)).all())
    item_feature_map = {int(item_id): dict(features or {}) for item_id, features in feature_rows}

    dataset: list[tuple[list[float], float, float]] = []
    positive_samples = 0
    for request_id, item_id in sample_rows:
        key = (int(request_id), int(item_id))
        action = latest_feedback.get(key, (None, None))[0]
        target, sample_weight = _target_from_feedback(action)
        if target > 0:
            positive_samples += 1
        item_features = item_feature_map.get(int(item_id), {})
        dataset.append((_item_feature_vector(item_features), target, sample_weight))

    stats = {
        "sample_count": len(dataset),
        "positive_samples": positive_samples,
        "feedback_rows": len(feedback_rows),
        "items_with_features": len(item_feature_map),
        "lookback_days": lookback_days,
    }
    return dataset, stats


def _weighted_logloss(samples: list[tuple[list[float], float, float]], weights: list[float]) -> float:
    loss_sum = 0.0
    total_weight = 0.0
    for vector, target, sample_weight in samples:
        prob = _sigmoid(_dot(weights, vector))
        prob = min(max(prob, 1e-6), 1.0 - 1e-6)
        loss = -target * math.log(prob) - (1.0 - target) * math.log(1.0 - prob)
        loss_sum += loss * sample_weight
        total_weight += sample_weight
    if total_weight <= 0:
        return 0.0
    return loss_sum / total_weight


def _train_recommendation_weights(
    samples: list[tuple[list[float], float, float]],
    epochs: int,
    learning_rate: float,
    l2: float,
    random_seed: int,
) -> tuple[dict[str, float], dict[str, Any]]:
    if not samples:
        raise ValueError("No samples available for training")

    weights = [
        DEFAULT_RANKING_WEIGHTS["bias"],
        DEFAULT_RANKING_WEIGHTS["purchase_count"],
        DEFAULT_RANKING_WEIGHTS["add_to_cart_count"],
        DEFAULT_RANKING_WEIGHTS["view_count"],
        DEFAULT_RANKING_WEIGHTS["positive_feedback"],
        DEFAULT_RANKING_WEIGHTS["negative_feedback"],
    ]

    rng = random.Random(random_seed)
    indices = list(range(len(samples)))
    loss_before = _weighted_logloss(samples, weights)
    loss_curve: list[float] = []

    for _ in range(epochs):
        rng.shuffle(indices)
        for idx in indices:
            vector, target, sample_weight = samples[idx]
            predicted = _sigmoid(_dot(weights, vector))
            error = (predicted - target) * sample_weight

            # Bias without regularization.
            weights[0] -= learning_rate * error * vector[0]
            for i in range(1, len(weights)):
                gradient = error * vector[i] + l2 * weights[i]
                weights[i] -= learning_rate * gradient
                weights[i] = max(-8.0, min(8.0, weights[i]))
        loss_curve.append(round(_weighted_logloss(samples, weights), 6))

    loss_after = _weighted_logloss(samples, weights)
    trained_weights = {
        "bias": round(weights[0], 6),
        "purchase_count": round(weights[1], 6),
        "add_to_cart_count": round(weights[2], 6),
        "view_count": round(weights[3], 6),
        "positive_feedback": round(weights[4], 6),
        "negative_feedback": round(weights[5], 6),
    }
    train_stats = {
        "loss_before": round(loss_before, 6),
        "loss_after": round(loss_after, 6),
        "loss_curve": loss_curve,
    }
    return trained_weights, train_stats


def _moderate_content(payload: ModerationCheckRequest) -> tuple[str, float, str]:
    content = f"{payload.title}\n{payload.description or ''}".lower()

    for pattern, reason_code in BANNED_PATTERNS:
        if pattern.search(content):
            return "reject", 0.98, reason_code

    text_len = len(content.strip())
    if text_len < 20:
        return "manual_review", 0.65, "low_content_volume"

    if payload.price is not None and payload.price <= 0:
        return "manual_review", 0.7, "non_positive_price"

    return "publish", 0.88, "ok"


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _bootstrap_default_models()


@app.get("/")
async def root():
    return {"service": "ai", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/events", response_model=AIEventOut, status_code=status.HTTP_201_CREATED)
async def ingest_event(event_in: AIEventCreate, db: AsyncSession = Depends(get_db)):
    event_repo = EventRepository(db)
    feature_repo = FeatureRepository(db)

    event = await event_repo.add_event(
        event_type=event_in.event_type,
        user_id=event_in.user_id,
        item_id=event_in.item_id,
        order_id=event_in.order_id,
        session_id=event_in.session_id,
        ts=event_in.ts,
        payload=event_in.payload,
    )
    await _apply_event_to_features(event_in, feature_repo)
    await db.commit()
    await db.refresh(event)
    return event


@app.get("/events", response_model=list[AIEventOut])
async def list_events(
    user_id: int | None = Query(default=None, ge=1),
    item_id: int | None = Query(default=None, ge=1),
    ts_from: datetime | None = None,
    ts_to: datetime | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    repo = EventRepository(db)
    return await repo.list_events(user_id=user_id, item_id=item_id, ts_from=ts_from, ts_to=ts_to, limit=limit)


@app.put("/features/items/{item_id}", status_code=status.HTTP_200_OK)
async def upsert_item_features(
    item_id: int,
    payload: ItemFeatureUpsert,
    db: AsyncSession = Depends(get_db),
):
    feature_repo = FeatureRepository(db)
    row = await feature_repo.upsert_item_features(
        item_id=item_id,
        category_id=payload.category_id,
        price=payload.price,
        stock=payload.stock,
        features_patch=payload.features,
    )
    await db.commit()
    return {
        "item_id": row.item_id,
        "category_id": row.category_id,
        "price": row.price,
        "stock": row.stock,
        "features": row.features,
    }


@app.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    payload: RecommendationRequest,
    db: AsyncSession = Depends(get_db),
):
    start = time.perf_counter()
    feature_repo = FeatureRepository(db)
    rec_repo = RecLogRepository(db)
    model_repo = ModelRegistryRepository(db)
    event_repo = EventRepository(db)

    active_model = await model_repo.get_active_model("recommendation")
    model_version = active_model.model_version if active_model else "heuristic-v1"
    model_metrics = active_model.metrics if active_model else None
    recommendations = await _generate_recommendations(payload, feature_repo, model_metrics=model_metrics)
    latency_ms = int((time.perf_counter() - start) * 1000)

    request_row = await rec_repo.create_request(
        user_id=payload.user_id,
        context=payload.context,
        category_id=payload.category_id,
        item_id=payload.item_id,
        model_version=model_version,
        latency_ms=latency_ms,
        ab_bucket=payload.ab_bucket,
    )
    await rec_repo.add_results(
        request_id=request_row.request_id,
        recommendations=[(rec.item_id, rec.score) for rec in recommendations],
    )

    await event_repo.add_event(
        event_type="RecommendationShown",
        user_id=payload.user_id,
        item_id=payload.item_id,
        ts=datetime.utcnow(),
        payload={
            "request_id": request_row.request_id,
            "context": payload.context,
            "recommended_item_ids": [item.item_id for item in recommendations],
        },
    )

    await db.commit()
    return RecommendationResponse(
        request_id=request_row.request_id,
        user_id=payload.user_id,
        context=payload.context,
        model_version=model_version,
        latency_ms=latency_ms,
        items=recommendations,
    )


@app.get("/recommendations", response_model=RecommendationResponse)
async def get_recommendations_get(
    user_id: int = Query(..., ge=1),
    context: Literal["catalog", "product", "cart"] = Query(default="catalog"),
    category_id: int | None = Query(default=None, ge=1),
    item_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    request = RecommendationRequest(
        user_id=user_id,
        context=context,
        category_id=category_id,
        item_id=item_id,
        limit=limit,
    )
    return await get_recommendations(request, db)


@app.post("/recommendations/feedback", status_code=status.HTTP_201_CREATED)
async def submit_recommendation_feedback(
    feedback_in: RecommendationFeedbackCreate,
    db: AsyncSession = Depends(get_db),
):
    rec_repo = RecLogRepository(db)
    event_repo = EventRepository(db)
    feature_repo = FeatureRepository(db)

    feedback = await rec_repo.add_feedback(
        request_id=feedback_in.request_id,
        user_id=feedback_in.user_id,
        item_id=feedback_in.item_id,
        action=feedback_in.action,
        ts=feedback_in.ts,
        payload=feedback_in.payload,
    )

    event_type = FEEDBACK_EVENT_MAP[feedback_in.action]
    await event_repo.add_event(
        event_type=event_type,
        user_id=feedback_in.user_id,
        item_id=feedback_in.item_id,
        ts=feedback_in.ts or datetime.utcnow(),
        payload={"request_id": feedback_in.request_id, **feedback_in.payload},
    )

    counter_key = "positive_feedback" if feedback_in.action == "clicked" else "negative_feedback"
    await _increment_item_counter(feature_repo, feedback_in.item_id, counter_key, delta=1.0)
    if feedback_in.action == "clicked":
        await _update_user_profile(feature_repo, feedback_in.user_id, event_type, None, INTERACTION_WEIGHTS["RecommendationClicked"])

    await db.commit()
    return {
        "id": feedback.id,
        "status": "recorded",
    }


@app.post("/moderation/check", response_model=ModerationDecisionOut)
async def moderation_check(
    payload: ModerationCheckRequest,
    db: AsyncSession = Depends(get_db),
):
    moderation_repo = ModerationRepository(db)
    model_repo = ModelRegistryRepository(db)
    event_repo = EventRepository(db)

    decision, confidence, reason_code = _moderate_content(payload)
    active_model = await model_repo.get_active_model("moderation")
    model_version = active_model.model_version if active_model else "rule-based-v1"

    req_row, decision_row = await moderation_repo.create_request_with_decision(
        item_id=payload.item_id,
        seller_id=payload.seller_id,
        title=payload.title,
        description=payload.description,
        category_id=payload.category_id,
        price=payload.price,
        payload=payload.payload,
        decision=decision,
        confidence=confidence,
        reason_code=reason_code,
        model_version=model_version,
    )

    await event_repo.add_event(
        event_type="ModerationDecision",
        user_id=payload.seller_id,
        item_id=payload.item_id,
        ts=datetime.utcnow(),
        payload={
            "request_id": req_row.id,
            "decision": decision_row.decision,
            "confidence": decision_row.confidence,
            "reason_code": decision_row.reason_code,
            "model_version": decision_row.model_version,
        },
    )

    await db.commit()
    return ModerationDecisionOut(
        request_id=req_row.id,
        decision=decision_row.decision,
        confidence=decision_row.confidence,
        reason_code=decision_row.reason_code,
        model_version=decision_row.model_version,
    )


@app.post("/moderation/appeals", status_code=status.HTTP_201_CREATED)
async def create_appeal(
    payload: ModerationAppealCreate,
    db: AsyncSession = Depends(get_db),
):
    repo = ModerationRepository(db)
    row = await repo.create_appeal(
        request_id=payload.request_id,
        seller_id=payload.seller_id,
        reason=payload.reason,
    )
    await db.commit()
    return {"appeal_id": row.id, "status": row.status}


@app.post("/moderation/appeals/{appeal_id}/result")
async def set_appeal_result(
    appeal_id: int,
    payload: ModerationAppealResultCreate,
    db: AsyncSession = Depends(get_db),
):
    repo = ModerationRepository(db)
    result = await repo.close_appeal_with_result(
        appeal_id=appeal_id,
        reviewer_id=payload.reviewer_id,
        result=payload.result,
        notes=payload.notes,
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appeal not found")

    await db.commit()
    return {"appeal_id": appeal_id, "result_id": result.id}


@app.post("/training/jobs", response_model=TrainingJobOut, status_code=status.HTTP_201_CREATED)
async def create_training_job(payload: TrainingJobCreate, db: AsyncSession = Depends(get_db)):
    repo = TrainingJobRepository(db)
    job = await repo.create_job(job_type=payload.job_type, parameters=payload.parameters)
    await db.commit()
    await db.refresh(job)
    return job


@app.patch("/training/jobs/{job_id}", response_model=TrainingJobOut)
async def update_training_job(job_id: int, payload: TrainingJobUpdate, db: AsyncSession = Depends(get_db)):
    repo = TrainingJobRepository(db)
    job = await repo.update_job(
        job_id=job_id,
        status=payload.status,
        metrics=payload.metrics,
        error_text=payload.error_text,
    )
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training job not found")

    await db.commit()
    await db.refresh(job)
    return job


@app.get("/training/jobs", response_model=list[TrainingJobOut])
async def list_training_jobs(
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    repo = TrainingJobRepository(db)
    return await repo.list_jobs(limit=limit)


@app.post("/training/recommendation/run", response_model=RecommendationTrainingRunResponse, status_code=status.HTTP_201_CREATED)
async def run_recommendation_training(
    payload: RecommendationTrainingRunRequest,
    db: AsyncSession = Depends(get_db),
):
    training_repo = TrainingJobRepository(db)
    model_repo = ModelRegistryRepository(db)

    parameters = payload.model_dump()
    job = await training_repo.create_job(job_type="recommendation", parameters=parameters)
    await training_repo.update_job(
        job_id=job.id,
        status="running",
        metrics={"stage": "loading_data"},
        error_text=None,
    )
    await db.flush()

    try:
        samples, sample_stats = await _load_recommendation_training_samples(
            db=db,
            lookback_days=payload.lookback_days,
            max_samples=payload.max_samples,
        )
        if sample_stats["sample_count"] < payload.min_samples:
            raise ValueError(
                f"Not enough recommendation samples. "
                f"Need at least {payload.min_samples} shown items."
            )
        if sample_stats["positive_samples"] < payload.min_positive_samples:
            raise ValueError(
                f"Not enough positive feedback samples. "
                f"Need at least {payload.min_positive_samples}, got {sample_stats['positive_samples']}."
            )

        trained_weights, train_stats = _train_recommendation_weights(
            samples=samples,
            epochs=payload.epochs,
            learning_rate=payload.learning_rate,
            l2=payload.l2,
            random_seed=payload.random_seed,
        )

        model_version = f"recs-sgd-v{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        model_metrics = {
            "source": "sgd_logistic_on_feedback",
            "ranking_weights": trained_weights,
            "context_weights": DEFAULT_CONTEXT_WEIGHTS,
            "training_parameters": parameters,
            "training_stats": {
                **sample_stats,
                **train_stats,
                "trained_at": datetime.utcnow().isoformat(),
            },
        }
        model = await model_repo.register_model(
            model_type="recommendation",
            model_version=model_version,
            metrics=model_metrics,
            artifact_uri=f"inline://{model_version}",
            is_active=payload.activate_model,
        )

        summary = {
            **sample_stats,
            **train_stats,
            "model_version": model_version,
            "is_active": payload.activate_model,
        }
        await training_repo.update_job(
            job_id=job.id,
            status="completed",
            metrics=summary,
            error_text=None,
        )
        await db.commit()
        await db.refresh(job)
        await db.refresh(model)
        return RecommendationTrainingRunResponse(
            job=job,
            model={
                "id": model.id,
                "model_type": model.model_type,
                "model_version": model.model_version,
                "metrics": model.metrics,
                "artifact_uri": model.artifact_uri,
                "is_active": model.is_active,
                "created_at": model.created_at.isoformat(),
            },
            summary=summary,
        )
    except Exception as exc:
        await training_repo.update_job(
            job_id=job.id,
            status="failed",
            metrics={"stage": "failed"},
            error_text=str(exc),
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Recommendation training failed: {exc}")


@app.post("/models/register", response_model=ModelOut, status_code=status.HTTP_201_CREATED)
async def register_model(payload: ModelRegisterCreate, db: AsyncSession = Depends(get_db)):
    repo = ModelRegistryRepository(db)
    model = await repo.register_model(
        model_type=payload.model_type,
        model_version=payload.model_version,
        metrics=payload.metrics,
        artifact_uri=payload.artifact_uri,
        is_active=payload.is_active,
    )
    await db.commit()
    await db.refresh(model)
    return model


@app.post("/models/{model_id}/activate", response_model=ModelOut)
async def activate_model(model_id: int, db: AsyncSession = Depends(get_db)):
    repo = ModelRegistryRepository(db)
    model = await repo.activate_model(model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

    await db.commit()
    await db.refresh(model)
    return model


@app.get("/models/active", response_model=ModelOut)
async def get_active_model(model_type: str = Query(...), db: AsyncSession = Depends(get_db)):
    repo = ModelRegistryRepository(db)
    model = await repo.get_active_model(model_type=model_type)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active model not found")
    return model


@app.get("/models", response_model=list[ModelOut])
async def list_models(
    model_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    repo = ModelRegistryRepository(db)
    return await repo.list_models(model_type=model_type, limit=limit)
