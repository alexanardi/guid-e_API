# app/utils.py
import openai
import os

def obtener_embedding(texto: str) -> list:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.Embedding.create(
        input=texto,
        model="text-embedding-ada-002"
    )
    return response["data"][0]["embedding"]
