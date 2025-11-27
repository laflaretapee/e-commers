from pydantic import BaseModel, EmailStr
from enum import Enum


class UserRole(str, Enum):
    customer = "customer"
    seller = "seller"
    admin = "admin"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.customer


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str

    class Config:
        from_attributes = True
