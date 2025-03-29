from fastapi import FastAPI
from app.db import get_connection
from app import nivel, curso, asignatura, calificacion, estudiante, observacion, archivo
from app import consultas

app = FastAPI()

app.include_router(nivel.router)
app.include_router(curso.router)
app.include_router(asignatura.router)
app.include_router(calificacion.router)
app.include_router(estudiante.router)
app.include_router(observacion.router)
app.include_router(archivo.router)
