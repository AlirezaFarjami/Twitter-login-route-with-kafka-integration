from kafka_consumer.database import users_collection
from bson import ObjectId
from fastapi import HTTPException, status

def get_user_id_by_username(username: str) -> ObjectId:
    """
    Fetch the user's MongoDB `_id` using their username.
    """
    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user["_id"]
