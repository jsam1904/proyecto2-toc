"""Lector de gramáticas: archivo .txt -> JSON.

Responsable: Javier.

Formato del .txt (una regla por línea):

    E -> T X
    X -> + T X | e
    F -> ( E ) | id

- Las alternativas se separan con `|` y los símbolos con espacios.
- `e` representa ε (debe ir sola en su alternativa).
- Se acepta `->` o `→` como flecha. Las líneas vacías y las que empiezan con `#` se ignoran.
- Una variable puede aparecer en varias líneas; sus producciones se juntan en orden.
- Variables: todo símbolo que aparece a la izquierda de una flecha. El resto son terminales.
- El símbolo inicial es la variable de la primera regla.

Representación JSON (un dict, la misma que usan simplificacion.py y cnf.py):

    {
      "inicial": "E",
      "variables": ["E", "X", ...],          # en orden de aparición
      "terminales": ["+", "id", ...],        # en orden de aparición
      "producciones": {"E": [["T", "X"]], "X": [["+", "T", "X"], []], ...}
    }

Una producción ε se guarda como la lista vacía `[]`.
"""

import json
import sys

EPSILON_TXT = "e"
EPSILON = "ε"


def construir(inicial, producciones):
    """Arma el dict de gramática recalculando variables y terminales.

    `producciones` es un dict variable -> lista de cuerpos. Una variable puede quedar
    temporalmente sin producciones (p. ej. tras quitar ε); sigue siendo variable hasta que
    la eliminación de inútiles la descarte. Se copian las listas para no compartir estado.
    """
    producciones = {a: [list(c) for c in cuerpos] for a, cuerpos in producciones.items()}
    variables = list(producciones)
    terminales = []
    for cuerpos in producciones.values():
        for cuerpo in cuerpos:
            for s in cuerpo:
                if s not in producciones and s not in terminales:
                    terminales.append(s)
    return {
        "inicial": inicial,
        "variables": variables,
        "terminales": terminales,
        "producciones": producciones,
    }


def leer_texto(texto):
    """Convierte el texto de una gramática a su dict JSON. Lanza ValueError si es inválida."""
    producciones = {}
    inicial = None
    for n, linea in enumerate(texto.splitlines(), start=1):
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        linea = linea.replace("→", "->")
        if "->" not in linea:
            raise ValueError(f"Línea {n}: falta la flecha '->'.")
        izquierda, derecha = linea.split("->", 1)
        cabeza = izquierda.strip()
        if not cabeza:
            raise ValueError(f"Línea {n}: falta la variable a la izquierda de '->'.")
        if len(cabeza.split()) != 1:
            raise ValueError(f"Línea {n}: a la izquierda debe haber una sola variable, no '{cabeza}'.")
        if cabeza == EPSILON_TXT:
            raise ValueError(f"Línea {n}: '{EPSILON_TXT}' representa ε y no puede ser una variable.")
        if inicial is None:
            inicial = cabeza
        cuerpos = producciones.setdefault(cabeza, [])
        for alternativa in derecha.split("|"):
            simbolos = alternativa.split()
            if not simbolos:
                raise ValueError(f"Línea {n}: hay una alternativa vacía; usa '{EPSILON_TXT}' para ε.")
            if EPSILON_TXT in simbolos:
                if len(simbolos) > 1:
                    raise ValueError(f"Línea {n}: '{EPSILON_TXT}' (ε) debe ir sola en su alternativa.")
                simbolos = []
            if simbolos not in cuerpos:
                cuerpos.append(simbolos)
    if inicial is None:
        raise ValueError("La gramática está vacía.")
    return construir(inicial, producciones)


def leer_archivo(ruta):
    with open(ruta, encoding="utf-8") as f:
        return leer_texto(f.read())


def a_texto(gramatica, epsilon=EPSILON_TXT):
    """Vuelve a escribir la gramática en el formato .txt (una línea por variable)."""
    lineas = []
    for a in gramatica["variables"]:
        cuerpos = gramatica["producciones"][a]
        alternativas = [" ".join(c) if c else epsilon for c in cuerpos]
        lineas.append(f"{a} -> {' | '.join(alternativas) or '∅'}")
    return "\n".join(lineas)


def a_json(gramatica):
    return json.dumps(gramatica, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python -m motor.gramatica gramaticas/1.txt")
        sys.exit(1)
    sys.stdout.reconfigure(encoding="utf-8")
    print(a_json(leer_archivo(sys.argv[1])))
