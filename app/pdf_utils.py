from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
import os

env = Environment(loader=FileSystemLoader("app/templates"))

def generar_pdf(contexto, nombre_pdf="informe.pdf"):
    template = env.get_template("informe_estudiante.html")
    html_content = template.render(contexto)

    output_path = f"/tmp/{nombre_pdf}"
    with open(output_path, "wb") as result_file:
        pisa_status = pisa.CreatePDF(html_content, dest=result_file)
        if pisa_status.err:
            raise Exception("❌ Error al generar PDF")
    return output_path

