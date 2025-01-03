import asyncio
import json
from aiokafka import AIOKafkaConsumer
import logging

KAFKA_BROKER_URL = "localhost:9092"
TOPIC_NAME = "twitter_login_requests"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def consume():
    consumer = AIOKafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=KAFKA_BROKER_URL,
        group_id="twitter_login_group",
        value_deserializer=lambda v: json.loads(v.decode('utf-8'))
    )
    await consumer.start()
    try:
        async for msg in consumer:
            logger.info(f"Consumed message: {msg.value}")
    finally:
        await consumer.stop()
        
if __name__ == "__main__":
    asyncio.run(consume())