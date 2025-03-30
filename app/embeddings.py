from app.db import get_connection
from app.utils import obtener_embedding

def buscar_fragmentos_relacionados(id_estudiante: str, pregunta: str, limite: int = 5):
    embedding = obtener_embedding(pregunta)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT "Fragmento", 1 - (Embedding <#> %s) AS similitud
        FROM "VectorArchivo"
        WHERE "IdEstudiante" = %s
        ORDER BY similitud DESC
        LIMIT %s
    """, (embedding, id_estudiante, limite))
    resultados = [{"fragmento": row[0], "similitud": row[1]} for row in cur.fetchall()]
    cur.close(); conn.close()
    return resultados
