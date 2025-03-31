from openai import OpenAI
import os


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generar_embedding(texto: str):
    response = client.embeddings.create(
        input=[texto],
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

def obtener_respuesta(prompt: str):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un asistente educativo experto en analizar información de estudiantes."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

