from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import os

# Carga la plantilla desde la carpeta templates
env = Environment(loader=FileSystemLoader("app/templates"))

def generar_pdf(contexto, nombre_pdf="informe.pdf"):
    template = env.get_template("informe_estudiante.html")
    html_content = template.render(contexto)
    ruta_salida = f"/tmp/{nombre_pdf}"  # ubicación temporal
    HTML(string=html_content).write_pdf(ruta_salida)
    return ruta_salida
