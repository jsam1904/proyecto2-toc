"""Lector de gramáticas: archivo .txt -> JSON.

Responsable: Javier.

Formato del .txt (una regla por línea):

    E -> T X
    X -> + T X | e
    F -> ( E ) | id

- Las alternativas se separan con `|` y los símbolos con espacios.
- `e` (o el símbolo unicode `ε`) representa ε (debe ir sola en su alternativa).
- Se acepta `->` o `→` como flecha. Las líneas vacías, las que empiezan con `#` y lo que
  sigue a un `#` en cualquier parte de la línea se ignoran (comentario).
- Una variable puede aparecer en varias líneas; sus producciones se juntan en orden.
- La cabeza (lo que va antes de la flecha) debe ser un solo nombre: empieza con una letra
  y sigue con letras, dígitos, `_` o `'` (p. ej. `E'` es válida).
- Variables: todo símbolo que aparece a la izquierda de una flecha. El resto son terminales.
- El símbolo inicial es la variable de la primera regla.
- Si un símbolo que empieza con mayúscula no tiene ninguna regla, se trata como terminal por
  convención (no es error); se reporta en "advertencias".
- El archivo puede empezar con BOM (﻿); se descarta antes de procesarlo.

Representación JSON (un dict, la misma que usan simplificacion.py y cnf.py):

    {
      "inicial": "E",
      "variables": ["E", "X", ...],          # en orden de aparición
      "terminales": ["+", "id", ...],        # en orden de aparición
      "producciones": {"E": [["T", "X"]], "X": [["+", "T", "X"], []], ...},
      "advertencias": ["A no tiene producciones; se trata como terminal.", ...]
    }

Una producción ε se guarda como la lista vacía `[]`.
"""

import json
import re
import sys

from motor.limites import MAX_CHARS_GRAMATICA, MAX_LINEAS, MAX_SIMBOLOS_POR_CUERPO

EPSILON_TXT = "e"
EPSILON = "ε"

_CABEZA_VALIDA = re.compile(r"^[A-Za-z][A-Za-z0-9_']*$")


def construir(inicial, producciones):
    """
    Arma el dict de gramática recalculando variables, terminales y advertencias.

    `producciones` es un dict variable -> lista de cuerpos. Una variable puede quedar
    temporalmente sin producciones (p. ej. tras quitar ε); sigue siendo variable hasta que
    la eliminación de inútiles la descarte. Se copian las listas para no compartir estado.
    Cada terminal que empieza con mayúscula genera una entrada en "advertencias".

    @param inicial: str  Símbolo inicial de la gramática.
    @param producciones: dict[str, list[list[str]]]  Variable -> lista de cuerpos.
    @return: dict  Gramática con las llaves inicial, variables, terminales, producciones
        y advertencias.
    """
    producciones = {a: [list(c) for c in cuerpos] for a, cuerpos in producciones.items()}
    variables = list(producciones)
    terminales = []
    for cuerpos in producciones.values():
        for cuerpo in cuerpos:
            for s in cuerpo:
                if s not in producciones and s not in terminales:
                    terminales.append(s)
    advertencias = [f"{t} no tiene producciones; se trata como terminal." for t in terminales if t[0].isupper()]
    return {
        "inicial": inicial,
        "variables": variables,
        "terminales": terminales,
        "producciones": producciones,
        "advertencias": advertencias,
    }


def leer_texto(texto):
    """
    Convierte el texto de una gramática a su dict JSON.

    Quita un posible BOM inicial, revisa los límites de motor/limites.py y valida cada
    línea: comentarios con `#`, flecha `->` o `→` (una sola), cabeza con nombre válido, y
    ε escrito como `e` o `ε` solo en su alternativa.

    @param texto: str  Contenido del archivo de gramática.
    @return: dict  Gramática en el formato de construir().
    @raises ValueError: si la gramática está vacía, excede un límite, o alguna línea no
        tiene el formato esperado.
    """
    texto = texto.lstrip("﻿")
    if len(texto) > MAX_CHARS_GRAMATICA:
        raise ValueError(f"La gramática tiene {len(texto)} caracteres; el máximo es {MAX_CHARS_GRAMATICA}.")
    lineas = texto.splitlines()
    if len(lineas) > MAX_LINEAS:
        raise ValueError(f"La gramática tiene {len(lineas)} líneas; el máximo es {MAX_LINEAS}.")

    producciones = {}
    inicial = None
    for n, linea in enumerate(lineas, start=1):
        if "#" in linea:
            linea = linea.split("#", 1)[0]
        linea = linea.strip()
        if not linea:
            continue
        linea = linea.replace("→", "->")
        if linea.count("->") > 1:
            raise ValueError(f"Línea {n}: hay más de una flecha '->'.")
        if "->" not in linea:
            raise ValueError(f"Línea {n}: falta la flecha '->'.")
        izquierda, derecha = linea.split("->", 1)
        cabeza = izquierda.strip()
        if not cabeza:
            raise ValueError(f"Línea {n}: falta la variable a la izquierda de '->'.")
        if len(cabeza.split()) != 1:
            raise ValueError(f"Línea {n}: a la izquierda debe haber una sola variable, no '{cabeza}'.")
        if cabeza in (EPSILON_TXT, EPSILON):
            raise ValueError(f"Línea {n}: '{cabeza}' representa ε y no puede ser una variable.")
        if not _CABEZA_VALIDA.match(cabeza):
            raise ValueError(
                f"Línea {n}: '{cabeza}' no es un nombre de variable válido; debe empezar con una letra "
                "y usar solo letras, dígitos, '_' o comilla simple."
            )
        if inicial is None:
            inicial = cabeza
        cuerpos = producciones.setdefault(cabeza, [])
        for alternativa in derecha.split("|"):
            simbolos = alternativa.split()
            if not simbolos:
                raise ValueError(f"Línea {n}: hay una alternativa vacía; usa '{EPSILON_TXT}' para ε.")
            if len(simbolos) > MAX_SIMBOLOS_POR_CUERPO:
                raise ValueError(
                    f"Línea {n}: el cuerpo '{alternativa.strip()}' tiene {len(simbolos)} símbolos; "
                    f"el máximo es {MAX_SIMBOLOS_POR_CUERPO}."
                )
            if EPSILON_TXT in simbolos or EPSILON in simbolos:
                if len(simbolos) > 1:
                    usado = EPSILON_TXT if EPSILON_TXT in simbolos else EPSILON
                    raise ValueError(f"Línea {n}: '{usado}' (ε) debe ir sola en su alternativa.")
                simbolos = []
            if simbolos not in cuerpos:
                cuerpos.append(simbolos)
    if inicial is None:
        raise ValueError("La gramática está vacía.")
    return construir(inicial, producciones)


def leer_archivo(ruta):
    """
    Lee un archivo de gramática y lo convierte a su dict JSON.

    @param ruta: str o Path  Ruta del archivo .txt.
    @return: dict  Gramática en el formato de construir().
    @raises ValueError: si el contenido no es una gramática válida.
    """
    with open(ruta, encoding="utf-8-sig") as f:
        return leer_texto(f.read())


def a_texto(gramatica, epsilon=EPSILON_TXT):
    """
    Vuelve a escribir la gramática en el formato .txt (una línea por variable).

    @param gramatica: dict  Gramática con el formato de construir().
    @param epsilon: str  Símbolo a usar para ε (por defecto "e").
    @return: str  Texto con una línea "A -> ..." por variable.
    """
    lineas = []
    for a in gramatica["variables"]:
        cuerpos = gramatica["producciones"][a]
        alternativas = [" ".join(c) if c else epsilon for c in cuerpos]
        lineas.append(f"{a} -> {' | '.join(alternativas) or '∅'}")
    return "\n".join(lineas)


def a_json(gramatica):
    """
    Serializa la gramática a JSON indentado, conservando los acentos y símbolos unicode.

    @param gramatica: dict  Gramática con el formato de construir().
    @return: str  Texto JSON.
    """
    return json.dumps(gramatica, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python -m motor.gramatica gramaticas/1.txt")
        sys.exit(1)
    sys.stdout.reconfigure(encoding="utf-8")
    print(a_json(leer_archivo(sys.argv[1])))
