# app/pdf_utils.py
import os
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")

env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

def generar_pdf(contexto: dict, nombre_archivo: str):
    template = env.get_template("informe.html")
    html = template.render(contexto)

    ruta_salida = os.path.join(STATIC_DIR, nombre_archivo)
    with open(ruta_salida, "wb") as f:
        pisa.CreatePDF(html, dest=f)

    print(f"✅ PDF generado en: {ruta_salida}")
    print(f"📄 Tamaño: {os.path.getsize(ruta_salida)} bytes")

    return nombre_archivo  # solo nombre del archivo, no ruta completa

