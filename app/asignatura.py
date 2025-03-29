from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.db import get_connection
import uuid

router = APIRouter()

class AsignaturaIn(BaseModel):
    Nombre: str

class AsignaturaOut(AsignaturaIn):
    IdAsignatura: str

@router.get("/asignaturas", response_model=List[AsignaturaOut])
def listar_asignaturas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT "IdAsignatura", "Nombre" FROM "Asignatura" ORDER BY "Nombre"')
    result = [AsignaturaOut(IdAsignatura=r[0], Nombre=r[1]) for r in cur.fetchall()]
    cur.close(); conn.close()
    return result

@router.post("/asignaturas", response_model=AsignaturaOut)
def crear_asignatura(data: AsignaturaIn):
    conn = get_connection()
    cur = conn.cursor()
    nuevo_id = str(uuid.uuid4())
    cur.execute('INSERT INTO "Asignatura" ("IdAsignatura", "Nombre") VALUES (%s, %s)', (nuevo_id, data.Nombre))
    conn.commit()
    cur.close(); conn.close()
    return AsignaturaOut(IdAsignatura=nuevo_id, Nombre=data.Nombre)

@router.get("/asignaturas/{id}", response_model=AsignaturaOut)
def obtener_asignatura(id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT "IdAsignatura", "Nombre" FROM "Asignatura" WHERE "IdAsignatura" = %s', (id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if row:
        return AsignaturaOut(IdAsignatura=row[0], Nombre=row[1])
    raise HTTPException(status_code=404, detail="Asignatura no encontrada")

@router.put("/asignaturas/{id}", response_model=AsignaturaOut)
def actualizar_asignatura(id: str, data: AsignaturaIn):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('UPDATE "Asignatura" SET "Nombre" = %s WHERE "IdAsignatura" = %s', (data.Nombre, id))
    if cur.rowcount == 0:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Asignatura no encontrada")
    conn.commit(); cur.close(); conn.close()
    return AsignaturaOut(IdAsignatura=id, Nombre=data.Nombre)

@router.delete("/asignaturas/{id}")
def eliminar_asignatura(id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM "Asignatura" WHERE "IdAsignatura" = %s', (id,))
    if cur.rowcount == 0:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Asignatura no encontrada")
    conn.commit(); cur.close(); conn.close()
    return {"message": "Asignatura eliminada correctamente"}
