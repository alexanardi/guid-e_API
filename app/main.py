from fastapi import FastAPI
from app.db import get_connection
from app import nivel

app = FastAPI()

app.include_router(nivel.router)

