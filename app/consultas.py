# from fastapi import APIRouter, HTTPException, Request
from fastapi import APIRouter, HTTPException, Request, Body
from app.schemas import PreguntaRequest
from app.embeddings import buscar_fragmentos_relacionados_sql
from app.embeddings import buscar_fragmentos_similares

from fastapi.responses import FileResponse
from app.db import get_connection
from app.pdf_utils import generar_pdf
from datetime import datetime
import unicodedata
import re

router = APIRouter()

@router.get("/estudiantes/{id}/resumen")
def resumen_estudiante(id: str):
    conn = get_connection()
    cur = conn.cursor()

    # Promedio general
    cur.execute("""
        SELECT ROUND(AVG("Nota")::numeric, 1) FROM "CalificacionEstudiante"
        WHERE "IdEstudiante" = %s
    """, (id,))
    promedio_general = cur.fetchone()[0]

    # Promedio por asignatura
    cur.execute("""
        SELECT a."Nombre", ROUND(AVG(c."Nota")::numeric, 1) as promedio
        FROM "CalificacionEstudiante" c
        JOIN "Asignatura" a ON c."IdAsignatura" = a."IdAsignatura"
        WHERE c."IdEstudiante" = %s
        GROUP BY a."Nombre"
        ORDER BY a."Nombre"
    """, (id,))
    promedios = [{"Asignatura": row[0], "Promedio": row[1]} for row in cur.fetchall()]

    # ObservacionEstudiantees
    cur.execute("""
        SELECT COUNT(*) FROM "ObservacionEstudiante"
        WHERE "IdEstudiante" = %s
    """, (id,))
    obs_total = cur.fetchone()[0]

    cur.close(); conn.close()

    return {
        "PromedioGeneral": promedio_general,
        "PromedioPorAsignatura": promedios,
        "CantidadObservacionEstudiantees": obs_total
    }

@router.get("/cursos/{id}/ranking")
def ranking_curso(id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT e."IdEstudiante", e."Nombre", e."Apellidos", ROUND(AVG(c."Nota")::numeric, 1) as promedio
        FROM "Estudiante" e
        JOIN "CalificacionEstudiante" c ON e."IdEstudiante" = c."IdEstudiante"
        WHERE e."IdCurso" = %s
        GROUP BY e."IdEstudiante"
        ORDER BY promedio DESC
    """, (id,))
    result = [
        {"IdEstudiante": r[0], "Nombre": r[1], "Apellidos": r[2], "Promedio": r[3]}
        for r in cur.fetchall()
    ]
    cur.close(); conn.close()
    return result


@router.get("/estudiantes/{id}/alertas")
def alertas_estudiante(id: str):
    conn = get_connection()
    cur = conn.cursor()

    # Promedio
    cur.execute("""
        SELECT AVG("Nota") FROM "CalificacionEstudiante"
        WHERE "IdEstudiante" = %s
    """, (id,))
    promedio = cur.fetchone()[0] or 0

    # ObservacionEstudiantees en el último mes
    cur.execute("""
        SELECT COUNT(*) FROM "ObservacionEstudiante"
        WHERE "IdEstudiante" = %s AND "Fecha" >= CURRENT_DATE - INTERVAL '30 days'
    """, (id,))
    observaciones = cur.fetchone()[0]

    alertas = []
    if promedio < 4.0:
        alertas.append("Promedio académico bajo")
    if observaciones >= 3:
        alertas.append("Muchas observaciones recientes")

    cur.close(); conn.close()
    return {
        "Promedio": round(promedio, 1),
        "ObservacionEstudiantees30Dias": observaciones,
        "Alertas": alertas
    }

@router.get("/estudiantes/{id}/ultimas-calificaciones")
def ultimas_notas(id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a."Nombre", c."Nota", c."Fecha"
        FROM "CalificacionEstudiante" c
        JOIN "Asignatura" a ON c."IdAsignatura" = a."IdAsignatura"
        WHERE c."IdEstudiante" = %s
        ORDER BY c."Fecha" DESC
        LIMIT 5
    """, (id,))
    result = [{"Asignatura": r[0], "Nota": float(r[1]), "Fecha": r[2]} for r in cur.fetchall()]
    cur.close(); conn.close()
    return result

@router.get("/estudiantes/{id}/informe")
def generar_informe(id: str, request: Request):  # <- se agregó "request"
    conn = get_connection()
    cur = conn.cursor()

    # Datos básicos del estudiante
    cur.execute("""
        SELECT e."Nombre", e."Apellidos", c."Nombre", n."Nombre"
        FROM "Estudiante" e
        LEFT JOIN "Curso" c ON e."IdCurso" = c."IdCurso"
        LEFT JOIN "Nivel" n ON c."IdNivel" = n."IdNivel"
        WHERE e."IdEstudiante" = %s
    """, (id,))
    datos = cur.fetchone()
    if not datos:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    nombre, apellidos, curso, nivel = datos

    # Promedio general
    cur.execute("""SELECT ROUND(AVG("Nota")::numeric, 1) FROM "CalificacionEstudiante" WHERE "IdEstudiante" = %s""", (id,))
    promedio_general = cur.fetchone()[0]

    # Promedios por asignatura
    cur.execute("""
        SELECT a."Nombre", ROUND(AVG(c."Nota")::numeric, 1)
        FROM "CalificacionEstudiante" c
        JOIN "Asignatura" a ON c."IdAsignatura" = a."IdAsignatura"
        WHERE c."IdEstudiante" = %s
        GROUP BY a."Nombre"
    """, (id,))
    promedios = [{"Asignatura": r[0], "Promedio": r[1]} for r in cur.fetchall()]

    # Últimas notas
    cur.execute("""
        SELECT a."Nombre", c."Nota", c."Fecha"
        FROM "CalificacionEstudiante" c
        JOIN "Asignatura" a ON c."IdAsignatura" = a."IdAsignatura"
        WHERE c."IdEstudiante" = %s
        ORDER BY c."Fecha" DESC
        LIMIT 5
    """, (id,))
    ultimas_notas = [{"Asignatura": r[0], "Nota": float(r[1]), "Fecha": r[2]} for r in cur.fetchall()]

    # Observaciones
    cur.execute("""SELECT "Fecha", "Texto" FROM "ObservacionEstudiante" WHERE "IdEstudiante" = %s ORDER BY "Fecha" DESC""", (id,))
    observaciones = [{"Fecha": r[0], "Texto": r[1]} for r in cur.fetchall()]

    # Alertas
    alertas = []
    if promedio_general and promedio_general < 4.0:
        alertas.append("Promedio académico bajo")
    cur.execute("""
        SELECT COUNT(*) FROM "ObservacionEstudiante"
        WHERE "IdEstudiante" = %s AND "Fecha" >= CURRENT_DATE - INTERVAL '30 days'
    """, (id,))
    if cur.fetchone()[0] >= 3:
        alertas.append("Muchas observaciones recientes")

    cur.close(); conn.close()

    contexto = {
        "nombre": nombre,
        "apellidos": apellidos,
        "curso": curso,
        "nivel": nivel,
        "promedio_general": promedio_general,
        "promedios": promedios,
        "ultimas_notas": ultimas_notas,
        "observaciones": observaciones,
        "alertas": alertas
    }

    # Generar nombre y PDF
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_pdf = f"informe_{nombre.lower()}_{apellidos.lower()}_{timestamp}.pdf".replace(" ", "_")
    nombre_archivo = generar_pdf(contexto, nombre_pdf)

    # URL del archivo PDF
    url = f"{request.base_url}static/{nombre_pdf}"

    return {"informe_url": url}

@router.post("/estudiantes/{id}/preguntar")
def preguntar_estudiante(id: str, data: PreguntaRequest = Body(...)):
    pregunta = data.pregunta
    id_archivo = data.id_archivo
    nombre_archivo = data.nombre_archivo

    if not pregunta:
        raise HTTPException(status_code=400, detail="Falta la pregunta")

    conn = get_connection()
    cur = conn.cursor()

    archivo = None
    if id_archivo:
        cur.execute("""
            SELECT "IdArchivo" FROM "ArchivoEstudiante"
            WHERE "IdArchivo" = %s AND "IdEstudiante" = %s
        """, (id_archivo, id))
        archivo = cur.fetchone()
    elif nombre_archivo:
        cur.execute("""
            SELECT "IdArchivo" FROM "ArchivoEstudiante"
            WHERE "NombreArchivo" = %s AND "IdEstudiante" = %s
        """, (nombre_archivo, id))
        archivo = cur.fetchone()

    if (id_archivo or nombre_archivo) and not archivo:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Archivo no encontrado para este estudiante")

    id_archivo_valido = archivo[0] if archivo else None

    from app.embeddings import buscar_fragmentos_relacionados_sql
    fragmentos = buscar_fragmentos_relacionados_sql(id, pregunta, cur, id_archivo_valido)

    if not fragmentos:
        cur.close(); conn.close()
        return {
            "respuesta": "No encontré información relevante en los archivos del estudiante para responder a tu pregunta.",
            "fragmentos_usados": []
        }

    contexto = "\n".join([f["fragmento"] for f in fragmentos])
    prompt = f"""Usa la siguiente información de contexto para responder la pregunta.

    Contexto:
    {contexto}

    Pregunta:
    {pregunta}

    Respuesta:"""

    from app.llm import obtener_respuesta
    respuesta = obtener_respuesta(prompt)

    cur.close(); conn.close()
    return {
        "respuesta": respuesta,
        "fragmentos_usados": fragmentos
    }


def buscar_fragmentos_relacionados(id_estudiante: str, pregunta: str, db, id_archivo: str = None):
    from app.llm import generar_embedding
    embedding_pregunta = generar_embedding(pregunta)

    query = "SELECT IdArchivo FROM ArchivoEstudiante WHERE IdEstudiante = %s"
    archivos = db.fetch_all(query, (id_estudiante,))

    if not archivos:
        return []

    lista_archivos = [a["IdArchivo"] for a in archivos]
    if id_archivo and id_archivo not in lista_archivos:
        return []

    archivos_filtrados = [id_archivo] if id_archivo else lista_archivos

    fragmentos = buscar_fragmentos_similares(embedding_pregunta, archivos_filtrados, db)
    return fragmentos

@router.get("/estudiantes/detalle")
def listar_estudiantes_con_curso():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT e."IdEstudiante", e."Nombre", e."Apellidos", 
               CONCAT(n."Nombre", ' - ', c."Nombre") as Curso
        FROM "Estudiante" e
        LEFT JOIN "Curso" c ON e."IdCurso" = c."IdCurso"
        LEFT JOIN "Nivel" n ON c."IdNivel" = n."IdNivel"
        ORDER BY e."Apellidos", e."Nombre"
    """)
    estudiantes = [
        {"IdEstudiante": r[0], "Nombre": r[1], "Apellidos": r[2], "Curso": r[3]}
        for r in cur.fetchall()
    ]
    cur.close(); conn.close()
    return estudiantes

@router.get("/estudiantes/{id}/detalle")
def obtener_estudiante_con_curso(id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT e."IdEstudiante", e."Nombre", e."Apellidos", 
               CONCAT(n."Nombre", ' - ', c."Nombre") as Curso
        FROM "Estudiante" e
        LEFT JOIN "Curso" c ON e."IdCurso" = c."IdCurso"
        LEFT JOIN "Nivel" n ON c."IdNivel" = n."IdNivel"
        WHERE e."IdEstudiante" = %s
    """, (id,))
    row = cur.fetchone()
    cur.close(); conn.close()

    if row:
        return {"IdEstudiante": row[0], "Nombre": row[1], "Apellidos": row[2], "Curso": row[3]}
    raise HTTPException(status_code=404, detail="Estudiante no encontrado")

@router.get("/estudiantes/{id}/observaciones")
def observaciones_por_estudiante(id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT "Fecha", "Texto"
        FROM "ObservacionEstudiante"
        WHERE "IdEstudiante" = %s
        ORDER BY "Fecha" DESC
    """, (id,))
    observaciones = [{"Fecha": r[0], "Texto": r[1]} for r in cur.fetchall()]
    cur.close(); conn.close()
    return observaciones
