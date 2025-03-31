from app.db import get_connection
from app.utils import obtener_embedding

def buscar_fragmentos_relacionados_sql(id_estudiante: str, pregunta: str, cur, id_archivo: str = None):
    from app.llm import generar_embedding
    embedding_pregunta = generar_embedding(pregunta)

    cur.execute("""
        SELECT "IdArchivo" FROM "ArchivoEstudiante"
        WHERE "IdEstudiante" = %s
    """, (id_estudiante,))
    archivos = cur.fetchall()
    if not archivos:
        return []

    lista_archivos = [a[0] for a in archivos]
    if id_archivo and id_archivo not in lista_archivos:
        return []

    archivos_filtrados = [id_archivo] if id_archivo else lista_archivos

    placeholders = ", ".join(["%s"] * len(archivos_filtrados))
    query = f"""
        SELECT 
            "Fragmento", 
            "Embedding" <-> %s AS distancia
        FROM "VectorArchivo"
        WHERE "IdArchivo" IN ({placeholders})
        ORDER BY "Embedding" <-> %s
        LIMIT 5
    """
    params = [embedding_pregunta] + archivos_filtrados + [embedding_pregunta]
    cur.execute(query, params)
    resultados = cur.fetchall()

    return [{"fragmento": r[0], "distancia": r[1]} for r in resultados]

def buscar_fragmentos_similares(embedding_pregunta, archivos_filtrados, db, top_k=5):
    if not archivos_filtrados:
        return []

    placeholders = ", ".join(["%s"] * len(archivos_filtrados))
    query = f"""
        SELECT 
            "Fragmento", 
            "Embedding" <-> %s::vector AS distancia
        FROM "VectorArchivo"
        WHERE "IdArchivo" IN ({placeholders})
        ORDER BY "Embedding" <-> %s::vector
        LIMIT {top_k}
    """
    params = [embedding_pregunta] + archivos_filtrados + [embedding_pregunta]
    resultados = db.fetch_all(query, params)

    return [{"fragmento": r["Fragmento"], "distancia": r["distancia"]} for r in resultados]
