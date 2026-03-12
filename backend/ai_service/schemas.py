from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AIEventCreate(BaseModel):
    event_type: str = Field(..., min_length=1, max_length=100)
    user_id: int | None = Field(None, ge=1)
    item_id: int | None = Field(None, ge=1)
    order_id: int | None = Field(None, ge=1)
    session_id: str | None = Field(None, max_length=120)
    ts: datetime | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AIEventOut(AIEventCreate):
    id: int
    ts: datetime

    class Config:
        from_attributes = True


class ItemFeatureUpsert(BaseModel):
    category_id: int | None = None
    price: float | None = None
    stock: int | None = None
    features: dict[str, Any] = Field(default_factory=dict)


class RecommendationRequest(BaseModel):
    user_id: int = Field(..., ge=1)
    context: Literal["catalog", "product", "cart"] = "catalog"
    category_id: int | None = Field(None, ge=1)
    item_id: int | None = Field(None, ge=1)
    item_ids: list[int] = Field(default_factory=list)
    limit: int = Field(10, ge=1, le=100)
    ab_bucket: str = Field("default", max_length=64)


class RecommendationItem(BaseModel):
    item_id: int
    score: float
    reason: str | None = None


class RecommendationResponse(BaseModel):
    request_id: int
    user_id: int
    context: str
    model_version: str
    latency_ms: int
    items: list[RecommendationItem]


class RecommendationFeedbackCreate(BaseModel):
    request_id: int = Field(..., ge=1)
    user_id: int = Field(..., ge=1)
    item_id: int = Field(..., ge=1)
    action: Literal["clicked", "skipped", "disliked"]
    ts: datetime | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class ModerationCheckRequest(BaseModel):
    item_id: int | None = Field(None, ge=1)
    seller_id: int | None = Field(None, ge=1)
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category_id: int | None = Field(None, ge=1)
    price: float | None = Field(None, ge=0)
    payload: dict[str, Any] = Field(default_factory=dict)


class ModerationDecisionOut(BaseModel):
    request_id: int
    decision: Literal["publish", "manual_review", "reject"]
    confidence: float
    reason_code: str
    model_version: str


class ModerationAppealCreate(BaseModel):
    request_id: int = Field(..., ge=1)
    seller_id: int = Field(..., ge=1)
    reason: str = Field(..., min_length=3)


class ModerationAppealResultCreate(BaseModel):
    reviewer_id: int | None = Field(None, ge=1)
    result: Literal["upheld", "reverted", "partially_upheld"]
    notes: str | None = None


class TrainingJobCreate(BaseModel):
    job_type: Literal["recommendation", "moderation"] = "recommendation"
    parameters: dict[str, Any] = Field(default_factory=dict)


class TrainingJobUpdate(BaseModel):
    status: Literal["queued", "running", "failed", "completed"]
    metrics: dict[str, Any] = Field(default_factory=dict)
    error_text: str | None = None


class TrainingJobOut(BaseModel):
    id: int
    job_type: str
    status: str
    parameters: dict[str, Any]
    metrics: dict[str, Any]
    error_text: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecommendationTrainingRunRequest(BaseModel):
    lookback_days: int = Field(30, ge=1, le=365)
    max_samples: int = Field(50000, ge=100, le=500000)
    min_samples: int = Field(100, ge=10, le=500000)
    epochs: int = Field(8, ge=1, le=100)
    learning_rate: float = Field(0.03, gt=0, le=1.0)
    l2: float = Field(0.001, ge=0, le=1.0)
    min_positive_samples: int = Field(20, ge=1, le=100000)
    activate_model: bool = True
    random_seed: int = Field(4322026, ge=1)


class RecommendationTrainingRunResponse(BaseModel):
    job: TrainingJobOut
    model: dict[str, Any]
    summary: dict[str, Any] = Field(default_factory=dict)


class ModelRegisterCreate(BaseModel):
    model_type: Literal["recommendation", "moderation"]
    model_version: str = Field(..., min_length=1, max_length=120)
    metrics: dict[str, Any] = Field(default_factory=dict)
    artifact_uri: str = Field(..., min_length=1, max_length=500)
    is_active: bool = False


class ModelOut(BaseModel):
    id: int
    model_type: str
    model_version: str
    metrics: dict[str, Any]
    artifact_uri: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
