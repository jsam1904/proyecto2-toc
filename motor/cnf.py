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
    """
    Busca un nombre libre a partir de `candidato`, agregando un número si ya está usado.

    @param candidato: str  Nombre preferido.
    @param usados: set[str]  Nombres ya ocupados (variables y terminales).
    @return: str  `candidato`, o `candidato` + número si no estaba libre.
    """
    if candidato not in usados:
        return candidato
    i = 1
    while f"{candidato}{i}" in usados:
        i += 1
    return f"{candidato}{i}"


def _nombre_terminal(t, usados):
    """
    Elige el nombre de la variable nueva para el terminal `t`.

    Usa el mnemotécnico de NOMBRES_TERMINALES si existe; si no, el terminal en
    mayúsculas, o "T_<t>" si ya está en mayúsculas o no es alfanumérico.

    @param t: str  Terminal a reemplazar.
    @param usados: set[str]  Nombres ya ocupados.
    @return: str  Nombre de variable libre para `t`.
    """
    candidato = NOMBRES_TERMINALES.get(t)
    if candidato is None:
        candidato = t.upper() if t.isalnum() and t.upper() != t else f"T_{t}"
    return _libre(candidato, usados)


def _nombre_cola(usados):
    """
    Elige el nombre de la variable nueva para una cola de binarización.

    Usa letras libres de la Z hacia la A; si se agotan, recurre a _libre("N1", ...).

    @param usados: set[str]  Nombres ya ocupados.
    @return: str  Nombre de variable libre para la cola.
    """
    for letra in reversed(ascii_uppercase):
        if letra not in usados:
            return letra
    return _libre("N1", usados)


def es_cnf(g):
    """
    Indica si toda producción de `g` ya es A -> B C (variables) o A -> a (terminal).

    Una gramática sin ninguna producción (p. ej. cuando su lenguaje es {ε}) cumple esto
    trivialmente, porque no hay ningún cuerpo que lo incumpla.

    @param g: dict  Gramática con el formato de motor/gramatica.py.
    @return: bool  True si `g` ya está en CNF.
    """
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
    """
    Revisa que `g` no tenga producciones ε ni unitarias antes de convertirla a CNF.

    @param g: dict  Gramática con el formato de motor/gramatica.py.
    @raises ValueError: si alguna variable tiene una producción ε o unitaria.
    """
    for a, cuerpos in g["producciones"].items():
        for c in cuerpos:
            if not c:
                raise ValueError(f"{a} tiene una producción ε; simplifica la gramática antes de CNF.")
            if es_unitaria(c, g):
                raise ValueError(
                    f"{a} -> {c[0]} es unitaria; simplifica la gramática antes de CNF."
                )


def _texto_cuerpo(c):
    """
    Junta los símbolos de un cuerpo con espacios, para los mensajes de "detalle".

    @param c: list[str]  Cuerpo de una producción.
    @return: str  Símbolos separados por espacios.
    """
    return " ".join(c)


def a_cnf(g):
    """
    Convierte una gramática simplificada a Forma Normal de Chomsky.

    Si `g` ya está en CNF (incluida una gramática sin producciones, caso {ε}), la deja
    intacta. Si no, primero reemplaza los terminales en cuerpos de longitud >= 2 por
    variables nuevas, y luego binariza los cuerpos de longitud >= 3.

    @param g: dict  Gramática simplificada (sin ε, sin unitarias, sin inútiles).
    @return: tuple[dict, list[dict]]  (gramatica_cnf, pasos), cada paso con el formato de
        motor/simplificacion.py: paso().
    @raises ValueError: si `g` tiene alguna producción ε o unitaria (no está simplificada).
    """
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
        """Variable que representa la cola `simbolos` (la reutiliza si ya existe)."""
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
