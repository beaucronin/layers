from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select, insert
from urllib.parse import urlparse

from .auth import (
    authenticate_user,
    create_access_token,
    username_from_token,
    get_user,
    get_password_hash,
    user_from_token,
)
from .schemas import (
    ObservationWrapper,
    FacilityObservation,
    TransportObservation,
    AssetObservation,
    LatLongLocation,
    ResourceObservation,
    ExtentObservation,
    AgricultureObservation
)
from .db import db, Users, ObservationEvents, Observations
from .models import UserCreate, Token, Interpretation, InterpretationRequest
from .util import enum_to_dict, extract_place_info

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


@app.get("/meta/facility-functions")
async def facility_functions(token: str = Depends(oauth2_scheme)):
    user = await user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return enum_to_dict(FacilityObservation.FacilityFunction, alpha=True)


@app.get("/meta/facility-processes")
async def facility_processes(token: str = Depends(oauth2_scheme)):
    user = await user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return enum_to_dict(FacilityObservation.FacilityProcess, alpha=True)


@app.get("/meta/asset-types")
async def asset_types(token: str = Depends(oauth2_scheme)):
    user = await user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    out = enum_to_dict(AssetObservation.ContainerType, alpha=True)
    out.update(enum_to_dict(AssetObservation.VehicleType, alpha=True))
    return out


@app.get("/meta/asset-configurations")
async def asset_configurations(token: str = Depends(oauth2_scheme)):
    user = await user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return enum_to_dict(AssetObservation.AssetConfiguration, alpha=True)


@app.get("/meta/transport-modes")
async def transport_modes(token: str = Depends(oauth2_scheme)):
    user = await user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return enum_to_dict(TransportObservation.TransportMode, alpha=True)


@app.get("/meta/agriculture-types")
async def agriculture_types(token: str = Depends(oauth2_scheme)):
    user = await user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return enum_to_dict(AgricultureObservation.AgricultureType, alpha=True)


@app.get("/meta/crop-types")
async def crop_types(token: str = Depends(oauth2_scheme)):
    user = await user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return enum_to_dict(AgricultureObservation.CropType, alpha=True)


@app.get("/meta/livestock-types")
async def livestock_types(token: str = Depends(oauth2_scheme)):
    user = await user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return enum_to_dict(AgricultureObservation.LiveStockType, alpha=True)


@app.get("/meta/boundary-types")
async def boundary_types(token: str = Depends(oauth2_scheme)):
    user = await user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return enum_to_dict(ExtentObservation.BoundaryType, alpha=True)


@app.get("/meta/landuse-types")
async def landuse_types(token: str = Depends(oauth2_scheme)):
    user = await user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return enum_to_dict(ExtentObservation.LandUseType, alpha=True)


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
            status_code=400, detail="Password must be at least 8 characters"
        )
    if password.isalpha():
        raise HTTPException(
            status_code=400, detail="Password must contain at least one number"
        )
    if password.isnumeric():
        raise HTTPException(
            status_code=400, detail="Password must contain at least one letter"
        )

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
        updated_at=datetime.now(),
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


@app.post(
    "/observations",
    responses={
        201: {"description": "Observation created"},
        400: {"description": "Invalid payload"},
    },
    status_code=201,
)
async def observations(
    observation: ObservationWrapper, token: str = Depends(oauth2_scheme)
):
    user = await user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

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
                payload=pld.dict(exclude_unset=True),
            )
            result = await db.execute(query)

    return {"msg": "success"}


@app.post("/interpretation", response_model=Interpretation)
async def interpretation(
    req: InterpretationRequest, token: str = Depends(oauth2_scheme)
):
    user = await user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    text = req.input

    try:
        if text.find("google.com/maps/place") > -1:
            result = extract_place_info(text)
            if result:
                return Interpretation(
                    input=text,
                    type="facility",
                    description=result["description"],
                    location=LatLongLocation(latitude=result["latitude"], longitude=result["longitude"])
                )
        else:
            raise HTTPException(status_code=404, detail="Interpretation not found")

    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid input: {exc}") from exc


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
