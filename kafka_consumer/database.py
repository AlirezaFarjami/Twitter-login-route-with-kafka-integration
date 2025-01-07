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
users_collection = db["users"]

#Helper functions
def create_user(user_data):
    """
    Inserts a user into the twitter_users collection.
    """
    return twitter_users_collection.insert_one(user_data).inserted_id

def create_task(task_data):
    """
    Inserts a task into the task_statuses collection.
    """
    return task_statuses_collection.insert_one(task_data).inserted_id