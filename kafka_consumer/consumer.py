import asyncio
import json
from aiokafka import AIOKafkaConsumer
import logging
from kafka_consumer.database import twitter_users_collection, task_statuses_collection, create_task, create_user
from pymongo.errors import PyMongoError

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
            await process_message(message=msg.value)
    finally:
        await consumer.stop()

async def process_message(message):
    """
    Process and store the message in MongoDB with a reference between user and task.
    """
    try:
        # Check if the user exists
        user = twitter_users_collection.find_one({"username": message["username"]})

        if not user:
            # Create the user if not exists
            user_data = {
                "username": message["username"],
                "password": message["password"],
                "phone_number": message["phone_number"],
                "email": message.get("email"),
            }
            user_id = create_user(user_data)
            logger.info(f"User created with ID: {user_id}")
        else:
            user_id = user["_id"]
            logger.info(f"User found with ID: {user_id}")

        # Create a task with a reference to the user
        task_data = {
            "task_id": message["task_id"],
            "user_id": user_id,
            "status": "pending"  # Default status for new tasks
        }
        task_id = create_task(task_data)
        logger.info(f"Task created with ID: {task_id}")

    except PyMongoError as e:
        logger.error(f"Error processing message: {e}")
    


if __name__ == "__main__":
    asyncio.run(consume())