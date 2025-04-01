from pydantic import BaseModel
from typing import Optional

class PreguntaRequest(BaseModel):
    pregunta: str
    id_archivo: Optional[str] = None
    nombre_archivo: Optional[str] = None
