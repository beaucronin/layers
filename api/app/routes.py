from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select, insert, update
from geoalchemy2 import Geometry

from .auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    user_from_token,
)
from .schemas import (
    ObservationEvent,
    FacilityObservation,
    TransportObservation,
    AssetObservation,
    LatLongLocation,
    ExtentObservation,
    AgricultureObservation,
)
from .db import db, Users, ObservationEvents, Observations, UserStats as UserStatsDB
from .models import (
    User,
    UserCreate,
    Token,
    Interpretation,
    InterpretationRequest,
    UserUpdate,
    UserStats as UserStatsModel,
)
from .util import enum_to_dict, extract_place_info, format_as_native, format_as_geojson

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


@app.get("/meta/agriculture-crop-types")
async def crop_types(token: str = Depends(oauth2_scheme)):
    user = await user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return enum_to_dict(AgricultureObservation.CropType, alpha=True)


@app.get("/meta/agriculture-livestock-types")
async def livestock_types(token: str = Depends(oauth2_scheme)):
    user = await user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return enum_to_dict(AgricultureObservation.LiveStockType, alpha=True)


@app.get("/meta/extent-boundary-types")
async def boundary_types(token: str = Depends(oauth2_scheme)):
    user = await user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return enum_to_dict(ExtentObservation.BoundaryType, alpha=True)


@app.get("/meta/extent-land-use-types")
async def landuse_types(token: str = Depends(oauth2_scheme)):
    user = await user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return enum_to_dict(ExtentObservation.LandUseType, alpha=True)


@app.get("/users/me")
async def user_info(token: str = Depends(oauth2_scheme)):
    user = await user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user.dict()


@app.patch("/users/me")
async def update_user(updated_user: UserUpdate, token: str = Depends(oauth2_scheme)):
    user = await user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # ensure username is not changed
    setattr(updated_user, "username", user.username)

    # remove None values
    d = updated_user.dict()
    for k, v in list(d.items()):
        if v is None:
            del d[k]

    # update user
    query = update(Users).where(Users.username == user.username).values(**d)
    await db.execute(query)

    # return updated user
    user = await user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user.dict()


# @app.get("/users/me/stats")
# async def user_stats(token: str = Depends(oauth2_scheme)) -> UserStatsModel:
#     user = await user_from_token(token, db)
#     if not user:
#         raise HTTPException(status_code=401, detail="Not authenticated")

#     return await get_user_stats(user)


# async def get_user_stats(user: User, max_age: int = 0) -> UserStatsModel:
#     latest_stats: UserStatsModel | None = await get_latest_user_stats(user)
#     if latest_stats:
#         return latest_stats
#     else:
#         return await compute_user_stats(user)


# async def get_latest_user_stats(user: User) -> UserStatsModel | None:
#     """Get the latest user stats from the database, or None if the user's stats have never been calculated ."""
#     query = (
#         select(UserStatsDB)
#         .where(UserStatsDB.username == user.username)
#         .order_by(UserStatsDB.created_at.desc())
#         .limit(1)
#     )
#     result = await db.fetch_one(query)
#     if result:
#         return None
#         # stats = UserStatsModel(**result)
#         # return stats
#     else:
#         return None


# async def compute_user_stats(user: User) -> UserStatsModel:
#     """Compute the user's stats, save them to the database, and return them."""
#     query = select(ObservationEvents).where(
#         ObservationEvents.observer == user.username
#         or ObservationEvents.observer == user.email
#     )
#     result = await db.fetch_all(query)

#     ins = insert(UserStatsDB).values()
#     await db.execute(ins)

#     stats = UserStatsModel()
#     return stats


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
    observation: ObservationEvent, token: str = Depends(oauth2_scheme)
):
    user = await user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return await _observations(observation)


@app.post(
    "/observations-open",
    responses={
        201: {"description": "Observation created"},
        400: {"description": "Invalid payload"},
    },
    status_code=201,
)
async def observations_open(observation: ObservationEvent):
    return await _observations(observation)


async def _observations(observation: ObservationEvent):
    if isinstance(observation.payload, list):
        count = len(observation.payload)
    else:
        count = 1

    async with db.transaction():
        geo = None
        if isinstance(observation.location, LatLongLocation):
            loc = observation.location
            geo = f'POINT({loc.longitude} {loc.latitude})'
        else:
            raise NotImplementedError("Only LatLongLocation is supported at the moment")
        
        query = insert(ObservationEvents).values(
            # user_id=user.username,
            observer=observation.observer,
            source=observation.source,
            observed_at=observation.observed_at,
            submitted_at=observation.submitted_at,
            location=observation.location.dict(),
            observation_count=count,
            geo=geo
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

@app.get("/observations")
async def get_observations(format: str = "native", token: str = Depends(oauth2_scheme)):
    """Get the observations for the current user, within a certain area, optionally of a certain type."""
    user = await user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    query = select(ObservationEvents).where(ObservationEvents.observer == user.username)
    result = await db.fetch_all(query)

    if format == "native":
        return format_as_native(result)
    elif format == "geojson":
        return format_as_geojson(result)
    else:
        raise HTTPException(status_code=400, detail="Invalid format")


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
                    location=LatLongLocation(
                        latitude=result["latitude"], longitude=result["longitude"]
                    ),
                )
        else:
            raise HTTPException(status_code=404, detail="Interpretation not found")

    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid input: {exc}") from exc
