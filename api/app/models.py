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
    email: Optional[str]
    fullname: Optional[str]
    disabled: Optional[str]


class UserInDB(User):
    password: str


class Reward(BaseModel):
    amount: int
    created_at: str

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


class UserStats(BaseModel):
    class Counts(BaseModel):
        assets: int
        facilities: int
        resources: int
        transports: int
        extents: int

    username: str
    created_at: str
    counts_alltime: Counts
    counts_1day: Counts
    counts_7days: Counts
    counts_30days: Counts   
    counts_90days: Counts
    counts_365days: Counts
    last_observation: str
