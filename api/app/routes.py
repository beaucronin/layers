import logging
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select, insert
from jose import JWTError

from .auth import authenticate_user, create_access_token, username_from_token, get_user, get_password_hash, user_from_token
from .schemas import ObservationWrapper
from .db import db, Users, ObservationEvents, Observations
from .models import UserCreate, Token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI()
app.debug = True


@app.on_event("startup")
async def startup():
    await db.connect()


@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()


@app.get("/")
async def root(token: str = Depends(oauth2_scheme)):
    user = await user_from_token(token, db)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if user:
        return {"msg": "hello, authenticated world", "user": user.username}
    else:
        raise credentials_exception


@app.get("/users/me")
async def user_info(token: str = Depends(oauth2_scheme)):
    username = username_from_token(token)
    if username:
        user = await get_user(db, username)
        return user.dict()


@app.post("/users", status_code=201) 
async def create_user(user: UserCreate):
    # check if user exists
    username = user.username
    query = select(Users).where(Users.username == username)
    result = await db.fetch_one(query)
    if result:
        raise HTTPException(status_code=400, detail="Username already exists")

    # check if password is valid
    password = user.password
    if len(password) < 8:
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters")
    if password.isalpha():
        raise HTTPException(
            status_code=400, detail="Password must contain at least one number")
    if password.isnumeric():
        raise HTTPException(
            status_code=400, detail="Password must contain at least one letter")

    # check if email exists
    email = user.email
    if email:
        query = select(Users).where(Users.email == email)
        result = await db.fetch_one(query)
        if result:
            raise HTTPException(status_code=400, detail="Email already exists")

    # hash password
    hashed_password = get_password_hash(password)

    # create user
    query = insert(Users).values(
        username=username,
        email=email,
        fullname=user.fullname,
        password=hashed_password,
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    result = await db.execute(query)


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})

    resp = {"access_token": access_token, "token_type": "bearer"}
    return resp 


@app.post("/observations", responses={201: {"description": "Observation created"}, 400: {"description": "Invalid payload"}}, status_code=201)
async def observations(observation: ObservationWrapper, token: str = Depends(oauth2_scheme)):
    user = await user_from_token(token, db)

    if isinstance(observation.payload, list):
        count = len(observation.payload)
    else:
        count = 1

    async with db.transaction():
        query = insert(ObservationEvents).values(
            # user_id=user.username,
            observer=observation.observer,
            source=observation.source,
            observed_at=observation.observed_at,
            submitted_at=observation.submitted_at,
            location=observation.location.dict(),
            observation_count=count,
        )
        result = await db.execute(query)
        event_id = result
        p = observation.payload
        if not isinstance(p, list):
            p = [p]

        for pld in p:
            query = insert(Observations).values(
                event_id=event_id,
                observation_type=pld.observation_type,
                payload=pld.dict(exclude_unset=True)
            )
            result = await db.execute(query)
    
    return {"msg": "success"}


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        username = username_from_token(token)
        if username is None:
            raise credentials_exception
    except Exception as exc:
        raise credentials_exception from exc
    user = get_user(db, username=username)
    if user is None:
        raise credentials_exception
    return user
