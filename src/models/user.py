from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from beanie import Document


class Register(BaseModel):
    username: str
    email: str
    phone_number: str
    password: str
    pic_url: Optional[str] = None


class Login(BaseModel):
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    username: str
    email: str
    phone_number: str
    pic_url: Optional[str] = None
    message: Optional[str] = None


# This is the model that will be saved to the database


class User(Document):
    username: str
    email: str
    phone_number: str
    password: str
    created_at: Optional[datetime] = None
    pic_url: Optional[str] = None
    verification_code: Optional[str] = None
    is_verified: bool = False


class UserUpdate(BaseModel):
    username: str
    email: str
    phone_number: str
    pic_url: str
