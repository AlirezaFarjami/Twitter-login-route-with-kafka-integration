from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from kafka_consumer.database import users_collection

# Configuration for JWT
JWT_SECRET_KEY = "CHANGE_THIS_SECRET"  # Same as the one in jwt_utils.py
JWT_ALGORITHM = "HS256"

# OAuth2PasswordBearer sets up the token extraction from the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Extract and validate the user from the JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode the token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Check if the user exists in the database
    user = users_collection.find_one({"username": username})
    if user is None:
        raise credentials_exception

    return user
