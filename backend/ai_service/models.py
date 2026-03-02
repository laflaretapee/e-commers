from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .db import Base


class AIEvent(Base):
    __tablename__ = "ai_events"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    event_type = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    item_id = Column(Integer, nullable=True, index=True)
    order_id = Column(Integer, nullable=True, index=True)
    session_id = Column(String(120), nullable=True, index=True)
    ts = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    payload = Column(JSON, nullable=False, default=dict)


class UserFeature(Base):
    __tablename__ = "user_features"

    user_id = Column(Integer, primary_key=True)
    features = Column(JSON, nullable=False, default=dict)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ItemFeature(Base):
    __tablename__ = "item_features"

    item_id = Column(Integer, primary_key=True)
    category_id = Column(Integer, nullable=True, index=True)
    price = Column(Float, nullable=True)
    stock = Column(Integer, nullable=True)
    features = Column(JSON, nullable=False, default=dict)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class RecRequest(Base):
    __tablename__ = "rec_requests"

    request_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    context = Column(String(64), nullable=False, index=True)
    category_id = Column(Integer, nullable=True, index=True)
    item_id = Column(Integer, nullable=True, index=True)
    ts = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    model_version = Column(String(120), nullable=False)
    latency_ms = Column(Integer, nullable=False, default=0)
    ab_bucket = Column(String(64), nullable=False, default="default")

    results = relationship(
        "RecResult",
        back_populates="request",
        cascade="all, delete-orphan",
    )


class RecResult(Base):
    __tablename__ = "rec_results"
    __table_args__ = (
        UniqueConstraint("request_id", "item_id", name="uq_rec_results_request_item"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    request_id = Column(
        BigInteger,
        ForeignKey("rec_requests.request_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_id = Column(Integer, nullable=False, index=True)
    rank = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)

    request = relationship("RecRequest", back_populates="results")


class RecFeedback(Base):
    __tablename__ = "rec_feedback"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    request_id = Column(
        BigInteger,
        ForeignKey("rec_requests.request_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(Integer, nullable=False, index=True)
    item_id = Column(Integer, nullable=False, index=True)
    action = Column(String(40), nullable=False, index=True)
    ts = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    payload = Column(JSON, nullable=False, default=dict)


class ModerationRequest(Base):
    __tablename__ = "moderation_requests"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    item_id = Column(Integer, nullable=True, index=True)
    seller_id = Column(Integer, nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(Integer, nullable=True, index=True)
    price = Column(Float, nullable=True)
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    decisions = relationship(
        "ModerationDecision",
        back_populates="request",
        cascade="all, delete-orphan",
    )


class ModerationDecision(Base):
    __tablename__ = "moderation_decisions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    request_id = Column(
        BigInteger,
        ForeignKey("moderation_requests.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    decision = Column(String(32), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    reason_code = Column(String(120), nullable=False)
    model_version = Column(String(120), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    request = relationship("ModerationRequest", back_populates="decisions")


class ModerationAppeal(Base):
    __tablename__ = "moderation_appeals"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    request_id = Column(
        BigInteger,
        ForeignKey("moderation_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seller_id = Column(Integer, nullable=False, index=True)
    reason = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="open", index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ModerationAppealResult(Base):
    __tablename__ = "moderation_appeal_results"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appeal_id = Column(
        BigInteger,
        ForeignKey("moderation_appeals.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    reviewer_id = Column(Integer, nullable=True, index=True)
    result = Column(String(40), nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_type = Column(String(80), nullable=False, index=True)
    status = Column(String(40), nullable=False, index=True, default="queued")
    parameters = Column(JSON, nullable=False, default=dict)
    metrics = Column(JSON, nullable=False, default=dict)
    error_text = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ModelRegistry(Base):
    __tablename__ = "model_registry"
    __table_args__ = (
        UniqueConstraint("model_type", "model_version", name="uq_model_type_version"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    model_type = Column(String(80), nullable=False, index=True)
    model_version = Column(String(120), nullable=False)
    metrics = Column(JSON, nullable=False, default=dict)
    artifact_uri = Column(String(500), nullable=False)
    is_active = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


Index("idx_ai_events_user_ts", AIEvent.user_id, AIEvent.ts)
Index("idx_ai_events_item_ts", AIEvent.item_id, AIEvent.ts)
Index("idx_rec_requests_user_context_ts", RecRequest.user_id, RecRequest.context, RecRequest.ts)
Index("idx_rec_feedback_user_action_ts", RecFeedback.user_id, RecFeedback.action, RecFeedback.ts)
