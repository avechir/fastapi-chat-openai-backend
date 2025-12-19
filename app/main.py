from fastapi import FastAPI
from dotenv import load_dotenv
from app.database import engine
import app.models as models
from app.routers import chats

load_dotenv()
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chat API")
app.include_router(chats.router)