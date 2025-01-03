from kafka_consumer.database import twitter_users_collection, task_statuses_collection
from pymongo.errors import PyMongoError
import logging
import asyncio
from aiokafka import AIOKafkaConsumer
import json

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
        async for message in consumer:
            logger.info(f"Consumed message: {message.value}")
            await process_message(message.value)
    finally:
        await consumer.stop()

async def process_message(message):
    """
    Process and store the message in MongoDB
    """
    try:
        # Extract details from the message
        user_data = {
            "username": message["username"],
            "password": message["password"],
            "phone_number": message["phone_number"],
            "email": message.get("email"),
        }
        task_status = {
            "task_id": message["task_id"],
            "status": "pending"  # Default status for new tasks
        }

        # Insert into MongoDB
        twitter_users_collection.insert_one(user_data)
        task_statuses_collection.insert_one(task_status)

        logger.info("Message processed and stored in MongoDB.")
    except PyMongoError as e:
        logger.error(f"Error storing message in MongoDB: {e}")

if __name__ == "__main__":
    asyncio.run(consume())
