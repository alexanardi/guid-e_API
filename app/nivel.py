from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.db import get_connection
import uuid

router = APIRouter()

class Nivel(BaseModel):
    IdNivel: str
    Nombre: str

class NivelCreate(BaseModel):
    Nombre: str

@router.get("/niveles", response_model=List[Nivel])
def listar_niveles():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT "IdNivel", "Nombre" FROM "Nivel" ORDER BY "Nombre"')
    niveles = [{"IdNivel": row[0], "Nombre": row[1]} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return niveles

@router.post("/niveles", response_model=Nivel)
def crear_nivel(nivel: NivelCreate):
    conn = get_connection()
    cur = conn.cursor()
    id_nuevo = str(uuid.uuid4())
    cur.execute('INSERT INTO "Nivel" ("IdNivel", "Nombre") VALUES (%s, %s)', (id_nuevo, nivel.Nombre))
    conn.commit()
    cur.close()
    conn.close()
    return {"IdNivel": id_nuevo, "Nombre": nivel.Nombre}

@router.get("/niveles/{id}", response_model=Nivel)
def obtener_nivel(id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT "IdNivel", "Nombre" FROM "Nivel" WHERE "IdNivel" = %s', (id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return {"IdNivel": row[0], "Nombre": row[1]}
    raise HTTPException(status_code=404, detail="Nivel no encontrado")

@router.put("/niveles/{id}", response_model=Nivel)
def actualizar_nivel(id: str, nivel: NivelCreate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('UPDATE "Nivel" SET "Nombre" = %s WHERE "IdNivel" = %s', (nivel.Nombre, id))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Nivel no encontrado")
    conn.commit()
    cur.close()
    conn.close()
    return {"IdNivel": id, "Nombre": nivel.Nombre}

@router.delete("/niveles/{id}")
def eliminar_nivel(id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM "Nivel" WHERE "IdNivel" = %s', (id,))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Nivel no encontrado")
    conn.commit()
    cur.close()
    conn.close()
    return {"mensaje": "Nivel eliminado correctamente"}
