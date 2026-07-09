from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    farmer = "farmer"
    admin = "admin"


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.farmer
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserInDB(BaseModel):
    id: str
    username: str
    password_hash: str
    role: UserRole
    full_name: str
    phone: Optional[str] = None
    is_active: bool = True


class UserResponse(BaseModel):
    id: str
    username: str
    role: UserRole
    full_name: str
    phone: Optional[str] = None
    is_active: bool = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    user_id: str
    full_name: str


class LoginRequest(BaseModel):
    username: str
    password: str
