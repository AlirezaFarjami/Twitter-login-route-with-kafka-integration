from pymongo.errors import PyMongoError
from aiokafka import AIOKafkaConsumer
from pymongo.errors import PyMongoError
import asyncio
import logging
import random
import json

from kafka_consumer.database import twitter_users_collection,task_statuses_collection ,create_task, create_user


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
    Process the task, simulate Twitter login and update the task status.
    If the user does not exist, create the user first.
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

        #Simulate Twitter login
        login_status = simulate_twitter_login()
        
        # Update or create the task status in the task_statuses collection
        task_data = {
            "task_id": message["task_id"],
            "user_id": user_id,
            "status": login_status  # Default status for new tasks
        }
        
        task_statuses_collection.update_one(
            {"task_id": message["task_id"]}, #Filter by task_id
            {"$set": task_data}, #Set new task data
            upsert=True
        )
        
        logger.info(f"Task {message['task_id']} processed with status: {login_status}")

    except PyMongoError as e:
        logger.error(f"Error processing message: {e}")
    

def simulate_twitter_login():
    """
    Simulates twitter login by randomly returning 'success' or 'failure'
    """
    return random.choice(["success","failure"])

if __name__ == "__main__":
    asyncio.run(consume())
