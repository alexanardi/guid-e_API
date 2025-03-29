from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.db import get_connection
import uuid
from datetime import date

router = APIRouter()

class CalificacionIn(BaseModel):
    IdEstudiante: str
    IdAsignatura: str
    Fecha: date
    Nota: float
    Anio: int

class CalificacionOut(CalificacionIn):
    IdCalificacion: str

@router.get("/calificaciones", response_model=List[CalificacionOut])
def listar_calificaciones():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT "IdCalificacion", "IdEstudiante", "IdAsignatura", "Fecha", "Nota", "Anio"
        FROM "CalificacionEstudiante"
        ORDER BY "Fecha" DESC
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [CalificacionOut(
        IdCalificacion=r[0], IdEstudiante=r[1], IdAsignatura=r[2],
        Fecha=r[3], Nota=float(r[4]), Anio=r[5]
    ) for r in rows]

@router.post("/calificaciones", response_model=CalificacionOut)
def crear_calificacion(data: CalificacionIn):
    conn = get_connection()
    cur = conn.cursor()
    nuevo_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO "CalificacionEstudiante"
        ("IdCalificacion", "IdEstudiante", "IdAsignatura", "Fecha", "Nota", "Anio")
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (nuevo_id, data.IdEstudiante, data.IdAsignatura, data.Fecha, data.Nota, data.Anio))
    conn.commit(); cur.close(); conn.close()
    return CalificacionOut(IdCalificacion=nuevo_id, **data.dict())

@router.get("/calificaciones/{id}", response_model=CalificacionOut)
def obtener_calificacion(id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT "IdCalificacion", "IdEstudiante", "IdAsignatura", "Fecha", "Nota", "Anio"
        FROM "CalificacionEstudiante"
        WHERE "IdCalificacion" = %s
    """, (id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if row:
        return CalificacionOut(
            IdCalificacion=row[0], IdEstudiante=row[1], IdAsignatura=row[2],
            Fecha=row[3], Nota=float(row[4]), Anio=row[5]
        )
    raise HTTPException(status_code=404, detail="Calificación no encontrada")

@router.put("/calificaciones/{id}", response_model=CalificacionOut)
def actualizar_calificacion(id: str, data: CalificacionIn):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE "CalificacionEstudiante"
        SET "IdEstudiante" = %s, "IdAsignatura" = %s, "Fecha" = %s, "Nota" = %s, "Anio" = %s
        WHERE "IdCalificacion" = %s
    """, (data.IdEstudiante, data.IdAsignatura, data.Fecha, data.Nota, data.Anio, id))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Calificación no encontrada")
    conn.commit(); cur.close(); conn.close()
    return CalificacionOut(IdCalificacion=id, **data.dict())

@router.delete("/calificaciones/{id}")
def eliminar_calificacion(id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM "CalificacionEstudiante" WHERE "IdCalificacion" = %s', (id,))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Calificación no encontrada")
    conn.commit(); cur.close(); conn.close()
    return {"message": "Calificación eliminada correctamente"}
