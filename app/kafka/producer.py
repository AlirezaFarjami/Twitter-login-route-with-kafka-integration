from aiokafka import AIOKafkaProducer
import os
import json
import asyncio
import logging

KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "localhost:9092")
TOPIC_NAME = os.getenv("KAFKA_TOPIC_NAME", "twitter_login_requests")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

producer = None

async def init_kafka():
    """
    Initialize the AIOKafkaProducer
    """
    global producer
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BROKER_URL,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )
    await producer.start()
    logger.info("Kafka producer started")
    
async def close_kafka():
    """
    Close the Kafka producer
    """
    await producer.stop()
    logger.info("Kafka producer stopped")
    
async def send_to_kafka(topic: str, message: dict):
    """
    Send a message to Kafka
    """
    global producer
    if producer is None:
        raise RuntimeError("Kafka producer is not initialized")
    
    try:
        await producer.send_and_wait(topic, value=message)
        logger.info(f"Message sent to Kafka: {message}")
    except Exception as e:
        logger.error(f"Error sending message to Kafka: {e}")