from typing import Optional
from pydantic import BaseModel
from .schemas import Location

class User(BaseModel):
    username: str
    email: str | None = None
    fullname: str | None = None
    disabled: bool | None = None


class UserCreate(BaseModel):
    username: str
    email: str | None = None
    fullname: str | None = None
    password: str


class UserUpdate(BaseModel):
    username: str
    email: str | None = None
    fullname: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class InterpretationRequest(BaseModel):
    input: str


class Interpretation(BaseModel):
    input: str
    type: str
    location: Optional[Location]
    description: Optional[str]
