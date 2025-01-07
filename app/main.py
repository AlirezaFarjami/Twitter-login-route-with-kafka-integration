from fastapi import FastAPI, Depends
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import aioredis
import uuid
from contextlib import asynccontextmanager

from app.models.twitter import TwitterLoginRequests
from app.kafka.producer import send_to_kafka, TOPIC_NAME, init_kafka, close_kafka


import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to handle startup and shutdown tasks.
    """
    # Startup: Initialize Redis
    redis = await aioredis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis)
    logger.info("Redis and FastAPI-Limiter initialized")
    await init_kafka()
    # Yield control to the application
    yield

    # Shutdown: Close Redis connection
    await redis.close()
    logger.info("Redis connection closed")

# Initialize the FastAPI app with the lifespan context
app = FastAPI(lifespan=lifespan)



@app.get("/")
def read_root():
    return{"message": "Welcome to the twitter Login API"}


@app.post("/twitter-login", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
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