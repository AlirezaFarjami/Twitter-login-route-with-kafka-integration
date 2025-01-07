from fastapi import FastAPI, Depends, HTTPException, status
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import aioredis
import uuid
from contextlib import asynccontextmanager

from app.models.twitter import TwitterLoginRequests
from app.models.user import UserRegister, UserLogin
from app.kafka.producer import send_to_kafka, TOPIC_NAME, init_kafka, close_kafka
from kafka_consumer.database import users_collection
from app.core.hash_utils import get_password_hash, verify_password
from app.core.jwt_utils import create_access_token
from app.core.dependencies import get_current_user

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

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegister):
    # 1. Check if username already exists
    existing_user = users_collection.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # 2. Hash the password
    hashed_password = get_password_hash(user_data.password)

    # 3. Insert the new user
    new_user = {
        "username": user_data.username,
        "hashed_password": hashed_password
    }
    users_collection.insert_one(new_user)

    # 4. Generate a JWT token for the newly registered user
    access_token = create_access_token(data={"sub": user_data.username})

    return {
        "message": "User registered successfully",
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post("/login")
async def login(user_data: UserLogin):
    # 1. Find the user by username
    user_doc = users_collection.find_one({"username": user_data.username})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # 2. Verify the password
    if not verify_password(user_data.password, user_doc["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # 3. If valid, create a JWT token
    access_token = create_access_token(data={"sub": user_data.username})
    
    # 4. Return the token
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post("/twitter-login", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def twitter_login(request: TwitterLoginRequests, current_user: dict = Depends(get_current_user)):
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