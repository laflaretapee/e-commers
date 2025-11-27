import os
import json
import asyncio
from typing import Optional

from aiokafka import AIOKafkaConsumer
from fastapi import FastAPI

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_ORDERS_TOPIC = os.getenv("KAFKA_ORDERS_TOPIC", "orders")

app = FastAPI(
    title="Notification Service",
    description="Слушает Kafka-топик заказов и логирует события.",
    version="1.0.0",
)

consumer: Optional[AIOKafkaConsumer] = None
consumer_task: Optional[asyncio.Task] = None


async def _consume_loop():
    assert consumer is not None
    async for msg in consumer:
        data = json.loads(msg.value.decode("utf-8"))
        print(f"[notification_service] Received order event: {data}")


@app.on_event("startup")
async def on_startup():
    global consumer, consumer_task
    consumer = AIOKafkaConsumer(
        KAFKA_ORDERS_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="notification-service",
    )
    await consumer.start()
    loop = asyncio.get_event_loop()
    consumer_task = loop.create_task(_consume_loop())


@app.on_event("shutdown")
async def on_shutdown():
    global consumer, consumer_task
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
    if consumer:
        await consumer.stop()


@app.get("/")
async def root():
    return {"service": "notification", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
