"""API FastAPI: expone POST /cyk.

Responsable: Angel. Por ahora /cyk responde 501 hasta que el motor esté listo.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Proyecto 2 — CNF y CYK")


class Peticion(BaseModel):
    gramatica: str
    oracion: str


@app.get("/salud")
def salud():
    return {"ok": True}


@app.post("/cyk")
def cyk(peticion: Peticion):
    raise HTTPException(status_code=501, detail="El motor CYK aún no está implementado.")
