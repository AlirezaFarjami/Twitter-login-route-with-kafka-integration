from pydantic import BaseModel, EmailStr, Field

class TwitterLoginRequests(BaseModel):
    username: str = Field(..., example="testuser")
    password: str = Field(..., examples="password123")
    phone_number: str = Field(..., example="1234567890")
    email: EmailStr | None = Field(None, examples="test@example.com")

