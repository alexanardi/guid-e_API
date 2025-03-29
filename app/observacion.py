from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.db import get_connection
from datetime import date
import uuid

router = APIRouter()

class ObservacionIn(BaseModel):
    IdEstudiante: str
    Fecha: date
    Texto: str

class ObservacionOut(ObservacionIn):
    IdObservacion: str

@router.get("/observaciones", response_model=List[ObservacionOut])
def listar_observaciones():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT "IdObservacion", "IdEstudiante", "Fecha", "Texto" FROM "Observacion" ORDER BY "Fecha" DESC')
    result = [ObservacionOut(IdObservacion=r[0], IdEstudiante=r[1], Fecha=r[2], Texto=r[3]) for r in cur.fetchall()]
    cur.close(); conn.close()
    return result

@router.post("/observaciones", response_model=ObservacionOut)
def crear_observacion(data: ObservacionIn):
    conn = get_connection()
    cur = conn.cursor()
    nuevo_id = str(uuid.uuid4())
    cur.execute('INSERT INTO "Observacion" ("IdObservacion", "IdEstudiante", "Fecha", "Texto") VALUES (%s, %s, %s, %s)',
                (nuevo_id, data.IdEstudiante, data.Fecha, data.Texto))
    conn.commit(); cur.close(); conn.close()
    return ObservacionOut(IdObservacion=nuevo_id, **data.dict())

@router.get("/observaciones/{id}", response_model=ObservacionOut)
def obtener_observacion(id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT "IdObservacion", "IdEstudiante", "Fecha", "Texto" FROM "Observacion" WHERE "IdObservacion" = %s', (id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if row:
        return ObservacionOut(IdObservacion=row[0], IdEstudiante=row[1], Fecha=row[2], Texto=row[3])
    raise HTTPException(status_code=404, detail="Observación no encontrada")

@router.put("/observaciones/{id}", response_model=ObservacionOut)
def actualizar_observacion(id: str, data: ObservacionIn):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('UPDATE "Observacion" SET "IdEstudiante" = %s, "Fecha" = %s, "Texto" = %s WHERE "IdObservacion" = %s',
                (data.IdEstudiante, data.Fecha, data.Texto, id))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Observación no encontrada")
    conn.commit(); cur.close(); conn.close()
    return ObservacionOut(IdObservacion=id, **data.dict())

@router.delete("/observaciones/{id}")
def eliminar_observacion(id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM "Observacion" WHERE "IdObservacion" = %s', (id,))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Observación no encontrada")
    conn.commit(); cur.close(); conn.close()
    return {"message": "Observación eliminada correctamente"}
