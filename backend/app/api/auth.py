from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
from uuid import uuid4

from app.api import users_store, sessions


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)


@router.post("/register")
def register(data: RegisterRequest):

    email = str(data.email).lower()

    if email in users_store:

        raise HTTPException(
            status_code=409,
            detail="User already exists"
        )

    user_id = str(uuid4())

    users_store[email] = {
        "id": user_id,
        "name": data.name,
        "email": email,
        "password": hash_password(data.password)
    }

    return {
        "message": "Registration successful",
        "user_id": user_id
    }


@router.post("/login")
def login(data: LoginRequest):

    email = str(data.email).lower()

    user = users_store.get(email)

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        data.password,
        user["password"]
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = str(uuid4())

    sessions[token] = user["id"]

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer"
    }


@router.post("/logout")
def logout(token: str):

    if token not in sessions:

        raise HTTPException(
            status_code=401,
            detail="Invalid session"
        )

    del sessions[token]

    return {
        "message": "Logout successful"
    }
