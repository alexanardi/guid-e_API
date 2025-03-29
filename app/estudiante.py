from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.db import get_connection
import uuid

router = APIRouter()

class EstudianteIn(BaseModel):
    Nombre: str
    Apellidos: str
    IdCurso: Optional[str] = None

class EstudianteOut(EstudianteIn):
    IdEstudiante: str

@router.get("/estudiantes", response_model=List[EstudianteOut])
def listar_estudiantes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT "IdEstudiante", "Nombre", "Apellidos", "IdCurso" FROM "Estudiante" ORDER BY "Apellidos"')
    result = [EstudianteOut(
        IdEstudiante=r[0], Nombre=r[1], Apellidos=r[2], IdCurso=r[3]
    ) for r in cur.fetchall()]
    cur.close(); conn.close()
    return result

@router.post("/estudiantes", response_model=EstudianteOut)
def crear_estudiante(data: EstudianteIn):
    conn = get_connection()
    cur = conn.cursor()
    nuevo_id = str(uuid.uuid4())
    cur.execute(
        'INSERT INTO "Estudiante" ("IdEstudiante", "Nombre", "Apellidos", "IdCurso") VALUES (%s, %s, %s, %s)',
        (nuevo_id, data.Nombre, data.Apellidos, data.IdCurso)
    )
    conn.commit(); cur.close(); conn.close()
    return EstudianteOut(IdEstudiante=nuevo_id, **data.dict())

@router.get("/estudiantes/{id}", response_model=EstudianteOut)
def obtener_estudiante(id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT "IdEstudiante", "Nombre", "Apellidos", "IdCurso" FROM "Estudiante" WHERE "IdEstudiante" = %s', (id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if row:
        return EstudianteOut(IdEstudiante=row[0], Nombre=row[1], Apellidos=row[2], IdCurso=row[3])
    raise HTTPException(status_code=404, detail="Estudiante no encontrado")

@router.put("/estudiantes/{id}", response_model=EstudianteOut)
def actualizar_estudiante(id: str, data: EstudianteIn):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        'UPDATE "Estudiante" SET "Nombre" = %s, "Apellidos" = %s, "IdCurso" = %s WHERE "IdEstudiante" = %s',
        (data.Nombre, data.Apellidos, data.IdCurso, id)
    )
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    conn.commit(); cur.close(); conn.close()
    return EstudianteOut(IdEstudiante=id, **data.dict())

@router.delete("/estudiantes/{id}")
def eliminar_estudiante(id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM "Estudiante" WHERE "IdEstudiante" = %s', (id,))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    conn.commit(); cur.close(); conn.close()
    return {"message": "Estudiante eliminado correctamente"}
