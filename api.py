from fastapi import FastAPI, Response, File, UploadFile, Request, Depends, Body, HTTPException
from fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from fastapi_jwt_auth import AuthJWT
from dotenv import dotenv_values
from hashlib import sha1
import requests
import pymongo
import os

config = dotenv_values(".env")

fileserverUrl = config["FILESERVERURL"]
secretKey = config["SECRETKEY"]
dbUrl = config["MONGOURL"]

app = FastAPI()


class File(BaseModel):
    data: bytes | str


class User(BaseModel):
    username: str
    password: str


class dbUserReq(BaseModel):
    username: str = Field(...)
    password: str = Field(...)
    permission: str = Field(...)


class dbUser(BaseModel):
    username: str = Field(...)
    hashedpass: str = Field(...)
    fileaccess: list = Field(...)
    permission: str = Field(...)


class Settings(BaseModel):
    authjwt_secret_key: str = secretKey


@AuthJWT.load_config
def get_config():
    return Settings()


client = pymongo.MongoClient(dbUrl)
db = client["dev"]['users']
print("Connected to the MongoDB database!")
db.create_index(
    [("username", pymongo.ASCENDING)],
    unique=True
)


def find_user(username):
    users = db.find({'username': username})
    for user in users:
        return user
    return None


def update_access(username, fileobj):
    db.find_one_and_update({'username': username}, {
                           '$push': {'fileaccess': fileobj}}, upsert=True)


@ app.on_event("shutdown")
def shutdown_db_client():
    client.close()


@ app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


@app.post("/login")
async def login(cred: User = Body(...), Authorize: AuthJWT = Depends()):
    try:
        user = find_user(cred.username)
        if user != None and user['hashedpass'] == user['hashedpass']:
            access_token = Authorize.create_access_token(
                subject=user["username"])
            return {"access_token": access_token}
    except:
        # If the request to the db fails, return 500 error.
        raise HTTPException(status_code=500, detail="Internal server error")
    # If credentials aren't correct, return 401 error.
    raise HTTPException(status_code=401, detail="Bad username or password")

def db_length_zero() : 
    users = db.find({})
    for user in users:
        return False
    return True

# Check users permissions. If user's permissions is admin, create the new user.
@app.post("/createuser")
async def create_user(cred: dbUserReq = Body(...), Authorize: AuthJWT = Depends()):
    try:
        # If there are 0 users, the first user to be created will be an admin.
        if not db_length_zero():
            Authorize.jwt_required()
            current_user = Authorize.get_jwt_subject()

            user = find_user(current_user)

            if user == None:
                raise HTTPException(status_code=401, detail="Unauthorized")

            if user['permission'] != 'admin':
                raise HTTPException(status_code=403, detail="Forbidden")
        else:
            cred.permission = "admin"
    except:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if cred.permission != "admin":
        cred.permission = "user"

    # Create User
    rec: dbUser = {
        'username': cred.username,
        'hashedpass': sha1(cred.password.encode()).hexdigest(),
        'fileaccess': [],
        'permission': cred.permission
    }

    try:
        db.insert_one(jsonable_encoder(rec))

        return JSONResponse(status_code=200, content={"detail": "Created account"})
    except:
        raise HTTPException(status_code=500, detail="Internal server error")


# Returns API Guide
@app.get("/")
async def read_root():
    r = requests.get(f"{fileserverUrl}/")
    return Response(content=r.content, media_type=r.headers['content-type'])


# Download bytes of owner/name.
@app.get("/file/")
async def read_file(name: str, Authorize: AuthJWT = Depends(), owner: str | None = None):
    targetFile = None
    try:
        Authorize.jwt_required()
        current_user = Authorize.get_jwt_subject()

        user = find_user(current_user)

        if user == None:
            raise HTTPException(status_code=401, detail="Unauthorized")

        if owner == None or owner == "":
            owner = user["username"]

        for file in user['fileaccess']:
            if file['name'] == name:
                targetFile = file
                break
    except Exception as e:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if targetFile == None:
        raise HTTPException(status_code=403, detail="Forbidden")

    location = targetFile['owner'] + '/' + targetFile['name']

    r = requests.get(f"{fileserverUrl}/{location}")
    return Response(content=r.content, media_type=r.headers['content-type'])


# Upload bytes of owner/name.
@app.post("/file/")
async def write_file(name: str, file: UploadFile, Authorize: AuthJWT = Depends(), owner: str | None = None):

    targetFile = None
    updateDb = False

    try:
        Authorize.jwt_required()
        current_user = Authorize.get_jwt_subject()
        user = find_user(current_user)

        if user == None:
            raise HTTPException(status_code=401, detail="Unauthorized")

        if owner == None or owner == "":
            owner = user["username"]

        for accessFile in user['fileaccess']:
            if accessFile['name'] == name and accessFile['owner'] == owner:
                if (accessFile['canwrite'] == False):
                    raise HTTPException(status_code=401, detail="Unauthorized")

                targetFile = accessFile
                break

        if targetFile == None:
            targetFile = {
                "name": f'{name}',
                "owner": user["username"],
                "canwrite": True
            }
            updateDb = True

    except Exception as e:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        location = targetFile["owner"] + '/' + targetFile['name']
        dirs = location.split('/')

        folder = ""
        for i in range(0, len(dirs) - 1):
            folder += '/' + dirs[i]
            if not os.path.exists(f"files/{folder}"):
                os.makedirs(f"files/{folder}")

        # Writes to file in bytes mode.
        with open(f"files/{location}", "wb") as f:
            f.write(await file.read())

        # Updates access list if the file is being written for the first time.
        if updateDb == True:
            update_access(user["username"], targetFile)

        return "Success!"
    except Exception as e:
        # Returns failed if file is badly formatted or already exists.
        raise HTTPException(status_code=500, detail="Internal server error")
        