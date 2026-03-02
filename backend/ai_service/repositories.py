from datetime import datetime

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    AIEvent,
    ItemFeature,
    ModelRegistry,
    ModerationAppeal,
    ModerationAppealResult,
    ModerationDecision,
    ModerationRequest,
    RecFeedback,
    RecRequest,
    RecResult,
    TrainingJob,
    UserFeature,
)


class EventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_event(
        self,
        event_type: str,
        user_id: int | None = None,
        item_id: int | None = None,
        order_id: int | None = None,
        session_id: str | None = None,
        ts: datetime | None = None,
        payload: dict | None = None,
    ) -> AIEvent:
        event = AIEvent(
            event_type=event_type,
            user_id=user_id,
            item_id=item_id,
            order_id=order_id,
            session_id=session_id,
            ts=ts or datetime.utcnow(),
            payload=payload or {},
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def list_events(
        self,
        user_id: int | None = None,
        item_id: int | None = None,
        ts_from: datetime | None = None,
        ts_to: datetime | None = None,
        limit: int = 100,
    ) -> list[AIEvent]:
        stmt = select(AIEvent).order_by(desc(AIEvent.ts)).limit(limit)
        if user_id is not None:
            stmt = stmt.where(AIEvent.user_id == user_id)
        if item_id is not None:
            stmt = stmt.where(AIEvent.item_id == item_id)
        if ts_from is not None:
            stmt = stmt.where(AIEvent.ts >= ts_from)
        if ts_to is not None:
            stmt = stmt.where(AIEvent.ts <= ts_to)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class FeatureRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_features(self, user_id: int) -> UserFeature | None:
        return await self.db.get(UserFeature, user_id)

    async def upsert_user_features(
        self,
        user_id: int,
        features_patch: dict | None = None,
    ) -> UserFeature:
        user_features = await self.db.get(UserFeature, user_id)
        if not user_features:
            user_features = UserFeature(user_id=user_id, features={})
            self.db.add(user_features)

        merged = dict(user_features.features or {})
        if features_patch:
            merged.update(features_patch)

        user_features.features = merged
        user_features.updated_at = datetime.utcnow()
        await self.db.flush()
        return user_features

    async def get_item_features(self, item_id: int) -> ItemFeature | None:
        return await self.db.get(ItemFeature, item_id)

    async def get_item_features_by_ids(self, item_ids: list[int]) -> list[ItemFeature]:
        if not item_ids:
            return []
        stmt = select(ItemFeature).where(ItemFeature.item_id.in_(item_ids))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def upsert_item_features(
        self,
        item_id: int,
        category_id: int | None = None,
        price: float | None = None,
        stock: int | None = None,
        features_patch: dict | None = None,
    ) -> ItemFeature:
        item_features = await self.db.get(ItemFeature, item_id)
        if not item_features:
            item_features = ItemFeature(item_id=item_id, features={})
            self.db.add(item_features)

        if category_id is not None:
            item_features.category_id = category_id
        if price is not None:
            item_features.price = price
        if stock is not None:
            item_features.stock = stock

        merged = dict(item_features.features or {})
        if features_patch:
            merged.update(features_patch)
        item_features.features = merged
        item_features.updated_at = datetime.utcnow()
        await self.db.flush()
        return item_features

    async def list_item_features(
        self,
        category_id: int | None = None,
        exclude_item_ids: set[int] | None = None,
        limit: int = 200,
    ) -> list[ItemFeature]:
        stmt = select(ItemFeature)
        if category_id is not None:
            stmt = stmt.where(ItemFeature.category_id == category_id)
        if exclude_item_ids:
            stmt = stmt.where(~ItemFeature.item_id.in_(exclude_item_ids))
        stmt = stmt.order_by(desc(ItemFeature.updated_at)).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class RecLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_request(
        self,
        user_id: int,
        context: str,
        category_id: int | None,
        item_id: int | None,
        model_version: str,
        latency_ms: int,
        ab_bucket: str,
    ) -> RecRequest:
        request = RecRequest(
            user_id=user_id,
            context=context,
            category_id=category_id,
            item_id=item_id,
            model_version=model_version,
            latency_ms=latency_ms,
            ab_bucket=ab_bucket,
            ts=datetime.utcnow(),
        )
        self.db.add(request)
        await self.db.flush()
        return request

    async def add_results(
        self,
        request_id: int,
        recommendations: list[tuple[int, float]],
    ) -> list[RecResult]:
        results: list[RecResult] = []
        for rank, (item_id, score) in enumerate(recommendations, start=1):
            row = RecResult(
                request_id=request_id,
                item_id=item_id,
                rank=rank,
                score=score,
            )
            self.db.add(row)
            results.append(row)

        await self.db.flush()
        return results

    async def add_feedback(
        self,
        request_id: int,
        user_id: int,
        item_id: int,
        action: str,
        ts: datetime | None = None,
        payload: dict | None = None,
    ) -> RecFeedback:
        feedback = RecFeedback(
            request_id=request_id,
            user_id=user_id,
            item_id=item_id,
            action=action,
            ts=ts or datetime.utcnow(),
            payload=payload or {},
        )
        self.db.add(feedback)
        await self.db.flush()
        return feedback


class ModerationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_request_with_decision(
        self,
        item_id: int | None,
        seller_id: int | None,
        title: str,
        description: str | None,
        category_id: int | None,
        price: float | None,
        payload: dict,
        decision: str,
        confidence: float,
        reason_code: str,
        model_version: str,
    ) -> tuple[ModerationRequest, ModerationDecision]:
        moderation_request = ModerationRequest(
            item_id=item_id,
            seller_id=seller_id,
            title=title,
            description=description,
            category_id=category_id,
            price=price,
            payload=payload,
            created_at=datetime.utcnow(),
        )
        self.db.add(moderation_request)
        await self.db.flush()

        moderation_decision = ModerationDecision(
            request_id=moderation_request.id,
            decision=decision,
            confidence=confidence,
            reason_code=reason_code,
            model_version=model_version,
            created_at=datetime.utcnow(),
        )
        self.db.add(moderation_decision)
        await self.db.flush()
        return moderation_request, moderation_decision

    async def create_appeal(
        self,
        request_id: int,
        seller_id: int,
        reason: str,
    ) -> ModerationAppeal:
        appeal = ModerationAppeal(
            request_id=request_id,
            seller_id=seller_id,
            reason=reason,
            status="open",
            created_at=datetime.utcnow(),
        )
        self.db.add(appeal)
        await self.db.flush()
        return appeal

    async def close_appeal_with_result(
        self,
        appeal_id: int,
        reviewer_id: int | None,
        result: str,
        notes: str | None,
    ) -> ModerationAppealResult | None:
        appeal = await self.db.get(ModerationAppeal, appeal_id)
        if not appeal:
            return None

        appeal.status = "closed"
        decision = ModerationAppealResult(
            appeal_id=appeal_id,
            reviewer_id=reviewer_id,
            result=result,
            notes=notes,
            created_at=datetime.utcnow(),
        )
        self.db.add(decision)
        await self.db.flush()
        return decision


class TrainingJobRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_job(
        self,
        job_type: str,
        parameters: dict,
    ) -> TrainingJob:
        job = TrainingJob(
            job_type=job_type,
            status="queued",
            parameters=parameters,
            metrics={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(job)
        await self.db.flush()
        return job

    async def update_job(
        self,
        job_id: int,
        status: str,
        metrics: dict,
        error_text: str | None,
    ) -> TrainingJob | None:
        job = await self.db.get(TrainingJob, job_id)
        if not job:
            return None
        job.status = status
        job.metrics = metrics
        job.error_text = error_text
        job.updated_at = datetime.utcnow()
        await self.db.flush()
        return job

    async def list_jobs(self, limit: int = 100) -> list[TrainingJob]:
        stmt = select(TrainingJob).order_by(desc(TrainingJob.created_at)).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class ModelRegistryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_model(
        self,
        model_type: str,
        model_version: str,
        metrics: dict,
        artifact_uri: str,
        is_active: bool,
    ) -> ModelRegistry:
        if is_active:
            await self.db.execute(
                update(ModelRegistry)
                .where(
                    ModelRegistry.model_type == model_type,
                    ModelRegistry.is_active.is_(True),
                )
                .values(is_active=False)
            )

        model = ModelRegistry(
            model_type=model_type,
            model_version=model_version,
            metrics=metrics,
            artifact_uri=artifact_uri,
            is_active=is_active,
            created_at=datetime.utcnow(),
        )
        self.db.add(model)
        await self.db.flush()
        return model

    async def activate_model(self, model_id: int) -> ModelRegistry | None:
        model = await self.db.get(ModelRegistry, model_id)
        if not model:
            return None

        await self.db.execute(
            update(ModelRegistry)
            .where(
                ModelRegistry.model_type == model.model_type,
                ModelRegistry.is_active.is_(True),
            )
            .values(is_active=False)
        )
        model.is_active = True
        await self.db.flush()
        return model

    async def get_active_model(self, model_type: str) -> ModelRegistry | None:
        stmt = (
            select(ModelRegistry)
            .where(
                ModelRegistry.model_type == model_type,
                ModelRegistry.is_active.is_(True),
            )
            .order_by(desc(ModelRegistry.created_at))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_models(self, model_type: str | None = None, limit: int = 100) -> list[ModelRegistry]:
        stmt = select(ModelRegistry)
        if model_type is not None:
            stmt = stmt.where(ModelRegistry.model_type == model_type)
        stmt = stmt.order_by(desc(ModelRegistry.created_at)).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
