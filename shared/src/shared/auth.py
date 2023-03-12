from fastapi import HTTPException, status
from typing import Optional
import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError
from sqlalchemy import select
from .models import UserInDB
from .db import db, Users

# Adapted from https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
# and https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
SECRET_KEY = os.getenv("LAYERS_SECRET_KEY", "")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_user(user_db, username: str) -> Optional[UserInDB]:
    query = select(Users).filter(Users.username == username)
    users = await user_db.fetch_all(query=query)
    if len(users) > 0:
        user = users[0]
        return UserInDB(**user._mapping)
    else:
        return None


async def authenticate_user(user_db, username: str, password: str) -> Optional[UserInDB]:
    user = await get_user(user_db, username)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


def username_from_token(token: str) -> Optional[str]:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload.get("sub")


async def user_from_token(token: str, user_db) -> Optional[UserInDB]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        username = username_from_token(token)
        print(username)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,   
            detail="Could not get username",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,   
            detail="username is none",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = await get_user(user_db, username)
        print(user)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,   
            detail="Could not get user",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    if not user:
        raise credentials_exception
    return user
        
