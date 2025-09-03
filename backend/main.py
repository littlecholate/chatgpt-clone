from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.util.init_db import create_tables
from app.routers.auth import authRouter
from app.routers.chat import chatRouter, messagesRouter
from app.util.protectRoute import get_current_user
from app.db.schema.user import UserOutput


@asynccontextmanager
async def lifespan(app : FastAPI):
    # Intializes the db tables when the application starts up
    create_tables()
    yield # seperation point
    # Application is closing


app = FastAPI(lifespan=lifespan)


origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 可以設定 ["*"] 代表允許所有
    allow_credentials=True,
    allow_methods=["*"],    # 允許所有 HTTP 方法: GET, POST, PUT, DELETE ...
    allow_headers=["*"],    # 允許所有自定義 headers
)

# Routers
app.include_router(router=authRouter, tags=["auth"], prefix="/auth")
app.include_router(router=chatRouter, tags=["chat"], prefix="/chat")
app.include_router(router=messagesRouter, tags=["chat"], prefix="/messages")


@app.get("/health")
def health():
    return {"status" : "Running...."}


@app.get("/protected")
def read_protected(user : UserOutput = Depends(get_current_user)):
    return {"data" : user}