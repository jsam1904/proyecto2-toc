"""API FastAPI: expone POST /gramatica y POST /cyk.

Responsable: Angel (/cyk) y Javier (/gramatica).
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from motor.cnf import a_cnf
from motor.gramatica import leer_texto
from motor.main import ejecutar
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
    """Pipeline completo (Angel): todo lo de /gramatica más la tokenización, la tabla
    CYK con sus pasos, el veredicto, el tiempo y el parse tree."""
    try:
        return ejecutar(peticion.gramatica, peticion.oracion)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
