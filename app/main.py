from fastapi import FastAPI
from app.db import get_connection
from app import nivel, curso

app = FastAPI()

app.include_router(nivel.router)
app.include_router(curso.router)
