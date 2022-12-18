from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from .auth import verify_password, get_password_hash
from .models import UserInDB, User
from ..schemas import ObservationWrapper


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI()


@app.get('/')
async def root(token: str = Depends(oauth2_scheme)):
    return {"msg": "hello world"}


@app.get('/users/me')
async def user_info():
    pass


@app.post('/observations')
async def observations(observation: ObservationWrapper):
    return observation


@app.post('/token')
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_info = get_user_info(form_data.username)
    if not user_info:
        raise HTTPException(
            status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_info)
    hashed_password = None
    if not hashed_password == user.hashed_password:
        raise HTTPException(
            status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}
