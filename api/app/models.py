from pydantic import BaseModel

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


class UserInDB(User):
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
