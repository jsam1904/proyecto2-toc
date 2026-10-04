"""API FastAPI: expone POST /cyk.

Responsable: Angel. Por ahora /cyk responde 501 hasta que el motor esté listo.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from motor.cnf import a_cnf
from motor.gramatica import leer_texto
from motor.simplificacion import simplificar

app = FastAPI(title="Proyecto 2 — CNF y CYK")


class Peticion(BaseModel):
    gramatica: str
    oracion: str


class PeticionGramatica(BaseModel):
    gramatica: str


@app.get("/salud")
def salud():
    return {"ok": True}


@app.post("/gramatica")
def gramatica(peticion: PeticionGramatica):
    """Fase 1 (Javier): lectura, simplificación y CNF, cada una con sus pasos."""
    try:
        g = leer_texto(peticion.gramatica)
        simple, pasos_simplificacion = simplificar(g)
        cnf, pasos_cnf = a_cnf(simple)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "gramatica": g,
        "simplificacion": pasos_simplificacion,
        "cnf": cnf,
        "pasos_cnf": pasos_cnf,
    }


@app.post("/cyk")
def cyk(peticion: Peticion):
    raise HTTPException(status_code=501, detail="El motor CYK aún no está implementado.")
