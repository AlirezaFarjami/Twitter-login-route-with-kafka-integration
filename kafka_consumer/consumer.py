from pymongo.errors import PyMongoError
from aiokafka import AIOKafkaConsumer
from pymongo.errors import PyMongoError
import asyncio
import logging
import random
import json
from bson import ObjectId
from kafka_consumer.database import twitter_users_collection, task_statuses_collection, create_task, create_user


KAFKA_BROKER_URL = "localhost:9092"
TOPIC_NAME = "twitter_login_requests"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import os
from cryptography.fernet import Fernet

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
fernet = Fernet(ENCRYPTION_KEY)

def encrypt_text(plaintext: str) -> bytes:
    """
    Encrypts the plaintext using Fernet and returns encrypted bytes.
    """
    return fernet.encrypt(plaintext.encode())

def decrypte(username: str) -> str:
    """
    Retrieves a user's encrypted password from the DB by username,
    decrypts it using the Fernet key, and returns the plaintext password.
    Returns None if the user or encrypted password is not found.
    """
    encryption_key = ENCRYPTION_KEY
    if not encryption_key:
        raise ValueError("No ENCRYPTION_KEY found in environment variables.")

    fernet = Fernet(encryption_key)

    user_doc = twitter_users_collection.find_one({"username": username})
    if not user_doc:
        return None  # User not found

    encrypted_password = user_doc.get("encrypted_password")
    if not encrypted_password:
        return None  # No password stored

    decrypted_bytes = fernet.decrypt(encrypted_password)
    return decrypted_bytes.decode()


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
    Process the task, simulate Twitter login, and update the task status.
    Include a reference to the user who made the request.
    """
    try:
        # Check if the Twitter user already exists
        twitter_user = twitter_users_collection.find_one({"username": message["username"]})

        if not twitter_user:
            # Create the Twitter user if not exists
            encrypted_password = encrypt_text(message["password"])
            user_data = {
                "username": message["username"],
                "encrypted_password": encrypted_password,
                "phone_number": message["phone_number"],
                "email": message.get("email"),
                "user_id": ObjectId(message["user_id"]),  # Reference to the user in the `users` collection
            }
            user_id = create_user(user_data)
            logger.info(f"Twitter user created with ID: {user_id}")
        else:
            user_id = twitter_user["_id"]
            logger.info(f"Twitter user found with ID: {user_id}")

        # Simulate Twitter login
        login_status = simulate_twitter_login()

        # Update or create the task status in the `task_statuses` collection
        task_data = {
            "task_id": message["task_id"],
            "user_id": ObjectId(message["user_id"]),  # Reference to the user in the `users` collection
            "status": login_status,
        }

        task_statuses_collection.update_one(
            {"task_id": message["task_id"]},  # Filter by task_id
            {"$set": task_data},  # Set new task data
            upsert=True
        )

        logger.info(f"Task {message['task_id']} processed with status: {login_status}")

    except PyMongoError as e:
        logger.error(f"Error processing message: {e}")



def simulate_twitter_login():
    """
    Simulates twitter login by randomly returning 'success' or 'failure'
    decrypte(username: str) can be called here
    """
    return random.choice(["success","failure"])

if __name__ == "__main__":
    asyncio.run(consume())