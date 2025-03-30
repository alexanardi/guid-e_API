from fastapi import FastAPI
from app.db import get_connection
from app import nivel, curso, asignatura, calificacion, estudiante, observacion, archivo
from app import consultas
from fastapi.staticfiles import StaticFiles


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


app.include_router(nivel.router)
app.include_router(curso.router)
app.include_router(asignatura.router)
app.include_router(calificacion.router)
app.include_router(estudiante.router)
app.include_router(observacion.router)
app.include_router(archivo.router)
app.include_router(consultas.router)

from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="GUID-E API",
        version="1.0.0",
        description="API para consultar información de estudiantes",
        routes=app.routes,
    )
    openapi_schema["servers"] = [
        {"url": "https://guid-eapi-production.up.railway.app"}
    ]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
