"""API FastAPI: expone POST /gramatica y POST /cyk.

Responsable: Angel (/cyk) y Javier (/gramatica).
"""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from motor.cnf import a_cnf
from motor.gramatica import leer_texto
from motor.limites import MAX_CHARS_ORACION
from motor.main import ejecutar
from motor.simplificacion import simplificar

app = FastAPI(title="Proyecto 2 — CNF y CYK")
logger = logging.getLogger(__name__)


class Peticion(BaseModel):
    gramatica: str
    oracion: str = Field(default="", max_length=MAX_CHARS_ORACION)


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
        "advertencias": g.get("advertencias", []),
    }


@app.post("/cyk")
def cyk(peticion: Peticion):
    """Pipeline completo (Angel): todo lo de /gramatica más la tokenización, la tabla
    CYK con sus pasos, el veredicto, el tiempo y el parse tree."""
    try:
        return ejecutar(peticion.gramatica, peticion.oracion)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.exception_handler(Exception)
async def manejador_errores_inesperados(request: Request, exc: Exception):
    """Responde 500 sin traceback ante cualquier error no previsto, y lo registra con
    logging (la causa inválida de entrada ya se maneja arriba como ValueError -> 400)."""
    logger.exception("Error interno del motor")
    return JSONResponse(status_code=500, content={"detail": "Error interno del motor"})
