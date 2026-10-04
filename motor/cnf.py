"""Conversión de la gramática a Forma Normal de Chomsky (CNF).

Responsable: Javier.

Recibe una gramática ya simplificada (sin ε, sin unitarias, sin inútiles; ver
simplificacion.py) y deja cada producción como A -> B C o A -> a:

1. Terminales en cuerpos de longitud >= 2: cada terminal t se reemplaza por una variable
   nueva T con T -> t.
2. Cuerpos de longitud >= 3: A -> X1 X2 ... Xn pasa a A -> X1 N con N -> X2 ... Xn,
   repitiendo hasta que todo cuerpo tenga dos símbolos. Una misma cola se reutiliza:
   si dos producciones terminan en "E R", ambas usan la misma variable nueva.

Nombres de las variables nuevas:
- Terminales: nombre mnemotécnico si existe ( "(" -> L, ")" -> R, "+" -> P, "*" -> M, ...)
  o el terminal en mayúsculas; si choca con un símbolo existente se le agrega un número.
- Colas de la binarización: letras libres de la Z hacia la A, luego N1, N2, ...

En la gramática resultante las variables nuevas van al final: primero las de la
binarización y después las de los terminales.

`a_cnf(g)` devuelve `(gramatica_cnf, pasos)` con el mismo formato de pasos que
`simplificar`.
"""

from string import ascii_uppercase

from motor.gramatica import construir
from motor.simplificacion import es_unitaria, paso

NOMBRES_TERMINALES = {
    "(": "L",
    ")": "R",
    "[": "LC",
    "]": "RC",
    "{": "LL",
    "}": "RL",
    "+": "P",
    "-": "N",
    "*": "M",
    "/": "D",
    "^": "W",
    "=": "I",
    ",": "C",
    ";": "PC",
    ".": "PT",
}


def _libre(candidato, usados):
    if candidato not in usados:
        return candidato
    i = 1
    while f"{candidato}{i}" in usados:
        i += 1
    return f"{candidato}{i}"


def _nombre_terminal(t, usados):
    candidato = NOMBRES_TERMINALES.get(t)
    if candidato is None:
        candidato = t.upper() if t.isalnum() and t.upper() != t else f"T_{t}"
    return _libre(candidato, usados)


def _nombre_cola(usados):
    for letra in reversed(ascii_uppercase):
        if letra not in usados:
            return letra
    return _libre("N1", usados)


def es_cnf(g):
    """True si toda producción es A -> B C (variables) o A -> a (terminal)."""
    prods = g["producciones"]
    for cuerpos in prods.values():
        for c in cuerpos:
            if len(c) == 1 and c[0] not in prods:
                continue
            if len(c) == 2 and c[0] in prods and c[1] in prods:
                continue
            return False
    return True


def _validar_simplificada(g):
    for a, cuerpos in g["producciones"].items():
        for c in cuerpos:
            if not c:
                raise ValueError(f"{a} tiene una producción ε; simplifica la gramática antes de CNF.")
            if es_unitaria(c, g):
                raise ValueError(
                    f"{a} -> {c[0]} es unitaria; simplifica la gramática antes de CNF."
                )


def _texto_cuerpo(c):
    return " ".join(c)


def a_cnf(g):
    """Convierte una gramática simplificada a CNF y devuelve `(gramatica_cnf, pasos)`."""
    _validar_simplificada(g)
    prods = g["producciones"]
    usados = set(g["variables"]) | set(g["terminales"])
    pasos = [paso("Gramática simplificada", "Punto de partida para la conversión a CNF.", g)]

    if es_cnf(g):
        pasos.append(
            paso(
                "Forma Normal de Chomsky",
                "Toda producción ya es A -> B C o A -> a; la gramática queda intacta.",
                g,
            )
        )
        return g, pasos

    # 1. Terminales dentro de cuerpos largos -> variables nuevas
    var_de_terminal = {}  # terminal -> variable nueva, en orden de creación
    nuevas = {}
    for a, cuerpos in prods.items():
        lista = []
        for c in cuerpos:
            if len(c) >= 2:
                cuerpo = []
                for s in c:
                    if s not in prods:
                        if s not in var_de_terminal:
                            var_de_terminal[s] = _nombre_terminal(s, usados)
                            usados.add(var_de_terminal[s])
                        s = var_de_terminal[s]
                    cuerpo.append(s)
                c = cuerpo
            lista.append(c)
        nuevas[a] = lista
    reglas_terminales = {v: [[t]] for t, v in var_de_terminal.items()}
    g1 = construir(g["inicial"], {**nuevas, **reglas_terminales})
    if var_de_terminal:
        detalle = "Variables nuevas para terminales en cuerpos de longitud >= 2: " + ", ".join(
            f"{v} -> {t}" for t, v in var_de_terminal.items()
        ) + "."
    else:
        detalle = "Ningún cuerpo largo contiene terminales; la gramática no cambia."
    pasos.append(paso("Reemplazar terminales en cuerpos largos", detalle, g1))

    # 2. Binarizar cuerpos de longitud >= 3
    var_de_cola = {}  # tupla de símbolos -> variable nueva, en orden de creación

    def cola(simbolos):
        if len(simbolos) == 1:
            return simbolos[0]
        clave = tuple(simbolos)
        if clave not in var_de_cola:
            var_de_cola[clave] = _nombre_cola(usados)
            usados.add(var_de_cola[clave])
            cola(simbolos[1:])  # registra primero las colas más largas
        return var_de_cola[clave]

    binarias = {}
    for a, cuerpos in nuevas.items():
        binarias[a] = [c if len(c) <= 2 else [c[0], cola(c[1:])] for c in cuerpos]
    reglas_colas = {v: [[k[0], cola(list(k[1:]))]] for k, v in var_de_cola.items()}
    final = construir(g["inicial"], {**binarias, **reglas_colas, **reglas_terminales})
    if var_de_cola:
        detalle = "Variables nuevas para las colas de cuerpos largos: " + ", ".join(
            f"{v} -> {_texto_cuerpo(k)}" for k, v in var_de_cola.items()
        ) + ". Cada una se reemplaza por su primer símbolo y otra variable hasta tener dos."
    else:
        detalle = "Ningún cuerpo tiene más de dos símbolos; la gramática no cambia."
    pasos.append(paso("Binarizar cuerpos largos", detalle, final))

    assert es_cnf(final)
    pasos.append(
        paso("Forma Normal de Chomsky", "Toda producción es ahora A -> B C o A -> a.", final)
    )
    return final, pasos
