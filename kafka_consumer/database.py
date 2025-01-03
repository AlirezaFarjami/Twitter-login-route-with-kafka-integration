from pymongo import MongoClient
import os

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "twitter_login_kafka")

# Initialize MongoDB Client
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

# Collections
twitter_users_collection = db["twitter_users"]
task_statuses_collection = db["task_statuses"]
