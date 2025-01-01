from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.models.twitter import TwitterLoginRequests
from app.kafka.producer import send_to_kafka, TOPIC_NAME, init_kafka, close_kafka

import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def app_lifespan(app: FastAPI):
    """
    Manage the Kafka producer lifecycle
    """
    logger.info("starting Kafka producer")
    await init_kafka()
    yield
    logger.info("stopping Kafka producer")
    await close_kafka()

app = FastAPI(lifespan=app_lifespan)

@app.get("/")

def read_root():
    return{"message": "Welcome to the twitter Login API"}


@app.post("/twitter-login")
async def twitter_login(request: TwitterLoginRequests):
    """
    Accepts user credentials and processes them via Kafka
    """
    #This line generates a unique task ID
    task_id = str(uuid.uuid4())
    
    #Preparing the message to send to Kafka
    message = request.model_dump() #Converting the Pydantic model to a python dictionary
    message["task_id"] = task_id
    logger.info(f"Sending message to Kafka: {message}")
    await send_to_kafka(TOPIC_NAME, message)
    return {"task_id": task_id}