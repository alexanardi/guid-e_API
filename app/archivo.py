from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.db import get_connection
from datetime import date
import uuid

router = APIRouter()

class ArchivoIn(BaseModel):
    IdEstudiante: str
    NombreArchivo: str
    Url: str
    FechaSubida: date
    Tipo: str

class ArchivoOut(ArchivoIn):
    IdArchivo: str

@router.get("/archivos", response_model=List[ArchivoOut])
def listar_archivos():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT "IdArchivo", "IdEstudiante", "NombreArchivo", "Url", "FechaSubida", "Tipo" FROM "ArchivoEstudiante" ORDER BY "FechaSubida" DESC')
    result = [ArchivoOut(
        IdArchivo=r[0], IdEstudiante=r[1], NombreArchivo=r[2], Url=r[3],
        FechaSubida=r[4], Tipo=r[5]
    ) for r in cur.fetchall()]
    cur.close(); conn.close()
    return result

@router.post("/archivos", response_model=ArchivoOut)
def crear_archivo(data: ArchivoIn):
    conn = get_connection()
    cur = conn.cursor()
    nuevo_id = str(uuid.uuid4())
    cur.execute('''
        INSERT INTO "ArchivoEstudiante" ("IdArchivo", "IdEstudiante", "NombreArchivo", "Url", "FechaSubida", "Tipo")
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (nuevo_id, data.IdEstudiante, data.NombreArchivo, data.Url, data.FechaSubida, data.Tipo))
    conn.commit(); cur.close(); conn.close()
    return ArchivoOut(IdArchivo=nuevo_id, **data.dict())

@router.get("/archivos/{id}", response_model=ArchivoOut)
def obtener_archivo(id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT "IdArchivo", "IdEstudiante", "NombreArchivo", "Url", "FechaSubida", "Tipo" FROM "ArchivoEstudiante" WHERE "IdArchivo" = %s', (id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if row:
        return ArchivoOut(
            IdArchivo=row[0], IdEstudiante=row[1], NombreArchivo=row[2],
            Url=row[3], FechaSubida=row[4], Tipo=row[5]
        )
    raise HTTPException(status_code=404, detail="Archivo no encontrado")

@router.delete("/archivos/{id}")
def eliminar_archivo(id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM "ArchivoEstudiante" WHERE "IdArchivo" = %s', (id,))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    conn.commit(); cur.close(); conn.close()
    return {"message": "Archivo eliminado correctamente"}

@router.get("/estudiantes/{id}/archivos", response_model=List[ArchivoOut])
def listar_archivos_estudiante(id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT "IdArchivo", "IdEstudiante", "NombreArchivo", "Url", "FechaSubida", "Tipo"
        FROM "ArchivoEstudiante"
        WHERE "IdEstudiante" = %s
        ORDER BY "FechaSubida" DESC
    ''', (id,))
    archivos = [ArchivoOut(
        IdArchivo=row[0], IdEstudiante=row[1], NombreArchivo=row[2],
        Url=row[3], FechaSubida=row[4], Tipo=row[5]
    ) for row in cur.fetchall()]
    cur.close(); conn.close()
    return archivos

