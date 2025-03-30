from fastapi import APIRouter, HTTPException
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
def generar_informe(id: str):
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

    # ObservacionEstudiantees
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

    # Generar nombre de archivo dinámico
    def slugify(text):
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        text = re.sub(r'[^\w\s-]', '', text).strip().lower()
        return re.sub(r'[-\s]+', '_', text)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_slug = slugify(nombre)
    apellidos_slug = slugify(apellidos)
    nombre_archivo = f"informe_{nombre_slug}_{apellidos_slug}_{timestamp}.pdf"


    ruta_pdf = generar_pdf(contexto, nombre_archivo)
    return FileResponse(ruta_pdf, filename=nombre_archivo, media_type="application/pdf")

