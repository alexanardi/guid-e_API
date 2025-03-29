# app/curso.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import get_connection

router = APIRouter()

class CursoIn(BaseModel):
    Nombre: str
    IdNivel: str

class CursoOut(CursoIn):
    IdCurso: str

@router.get("/cursos", response_model=list[CursoOut])
def listar_cursos():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""SELECT "IdCurso", "Nombre", "IdNivel" FROM "Curso" ORDER BY "Nombre" """)
    cursos = [CursoOut(IdCurso=r[0], Nombre=r[1], IdNivel=r[2]) for r in cur.fetchall()]
    cur.close(); conn.close()
    return cursos

@router.post("/cursos", response_model=CursoOut)
def crear_curso(data: CursoIn):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""INSERT INTO "Curso" ("Nombre", "IdNivel") VALUES (%s, %s) RETURNING "IdCurso" """,
                (data.Nombre, data.IdNivel))
    nuevo_id = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return CursoOut(IdCurso=nuevo_id, **data.dict())

@router.get("/cursos/{id}", response_model=CursoOut)
def obtener_curso(id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""SELECT "IdCurso", "Nombre", "IdNivel" FROM "Curso" WHERE "IdCurso" = %s""", (id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if row:
        return CursoOut(IdCurso=row[0], Nombre=row[1], IdNivel=row[2])
    raise HTTPException(status_code=404, detail="Curso no encontrado")

@router.put("/cursos/{id}", response_model=CursoOut)
def actualizar_curso(id: str, data: CursoIn):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""UPDATE "Curso" SET "Nombre" = %s, "IdNivel" = %s WHERE "IdCurso" = %s""",
                (data.Nombre, data.IdNivel, id))
    if cur.rowcount == 0:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    conn.commit(); cur.close(); conn.close()
    return CursoOut(IdCurso=id, **data.dict())

@router.delete("/cursos/{id}")
def eliminar_curso(id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""DELETE FROM "Curso" WHERE "IdCurso" = %s""", (id,))
    if cur.rowcount == 0:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    conn.commit(); cur.close(); conn.close()
    return {"message": "Curso eliminado correctamente"}
