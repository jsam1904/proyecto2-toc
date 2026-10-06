"""Simplificación: elimina producciones ε, unitarias y símbolos inútiles.

Responsable: Javier.

Se aplica en el orden clásico (Hopcroft-Ullman), que garantiza que ningún paso
reintroduce lo que quitó uno anterior:

1. Producciones ε: se calculan los anulables y cada cuerpo se reemplaza por todas sus
   variantes omitiendo anulables (menos la variante vacía).
2. Producciones unitarias A -> B: se sustituyen por las producciones no unitarias de
   todas las variables alcanzables desde A por cadenas de unitarias.
3. Símbolos inútiles: primero los no generadores y luego los inalcanzables.

`simplificar(g)` devuelve `(gramatica, pasos)`. Cada paso es un dict
`{"titulo", "detalle", "gramatica", "texto"}` con una foto de la gramática tras el paso,
listo para recorrerse en el componente <Pasos> del frontend.
"""

from itertools import product

from motor.gramatica import EPSILON, a_texto, construir
from motor.limites import MAX_ANULABLES_POR_CUERPO


def paso(titulo, detalle, gramatica):
    """
    Arma el dict de un paso del pipeline para el frontend y el CLI.

    @param titulo: str  Nombre del paso.
    @param detalle: str  Explicación de lo que hizo este paso.
    @param gramatica: dict  Gramática resultante, con el formato de construir().
    @return: dict  {"titulo", "detalle", "gramatica", "texto"}.
    """
    return {
        "titulo": titulo,
        "detalle": detalle,
        "gramatica": gramatica,
        "texto": a_texto(gramatica, epsilon=EPSILON),
    }


def _conjunto(simbolos):
    """
    Formatea una lista de símbolos como conjunto matemático para los mensajes de "detalle".

    @param simbolos: list[str]  Símbolos a mostrar.
    @return: str  "{a, b, c}", o "∅" si la lista está vacía.
    """
    return "{" + ", ".join(simbolos) + "}" if simbolos else "∅"


def anulables(g):
    """
    Calcula las variables anulables de la gramática (las que derivan ε).

    Repite vueltas agregando A si algún cuerpo de A tiene solo símbolos anulables, hasta
    que una vuelta no agregue nada.

    @param g: dict  Gramática con el formato de motor/gramatica.py.
    @return: list[str]  Variables anulables, en el orden de g["variables"].
    """
    prods = g["producciones"]
    nulos = set()
    cambio = True
    while cambio:
        cambio = False
        for a, cuerpos in prods.items():
            if a not in nulos and any(all(s in nulos for s in c) for c in cuerpos):
                nulos.add(a)
                cambio = True
    return [a for a in g["variables"] if a in nulos]


def eliminar_epsilon(g):
    """
    Quita las producciones ε, reemplazando cada cuerpo por todas sus variantes sin los
    símbolos anulables (menos la variante vacía).

    Antes de generar las variantes de un cuerpo, revisa cuántos de sus símbolos son
    anulables: si supera MAX_ANULABLES_POR_CUERPO, lanza el error en vez de generar las
    2^k combinaciones.

    @param g: dict  Gramática con el formato de motor/gramatica.py.
    @return: dict  Gramática sin producciones ε.
    @raises ValueError: si un cuerpo tiene más de MAX_ANULABLES_POR_CUERPO símbolos anulables.
    """
    nulos = set(anulables(g))
    nuevas = {}
    for a, cuerpos in g["producciones"].items():
        lista = []
        for cuerpo in cuerpos:
            n_anulables = sum(1 for s in cuerpo if s in nulos)
            if n_anulables > MAX_ANULABLES_POR_CUERPO:
                cuerpo_txt = " ".join(cuerpo) if cuerpo else "ε"
                raise ValueError(
                    f"La producción {a} -> {cuerpo_txt} tiene {n_anulables} símbolos anulables "
                    f"(máximo {MAX_ANULABLES_POR_CUERPO}); redúcela antes de simplificar."
                )
            # Para cada anulable: conservarlo u omitirlo. product() da primero el cuerpo completo.
            opciones = [[(s,), ()] if s in nulos else [(s,)] for s in cuerpo]
            for eleccion in product(*opciones):
                variante = [s for parte in eleccion for s in parte]
                if variante and variante not in lista:
                    lista.append(variante)
        nuevas[a] = lista
    return construir(g["inicial"], nuevas)


def pares_unitarios(g):
    """
    Calcula los pares unitarios de cada variable.

    Hace un BFS desde A siguiendo solo producciones A -> B (B variable) para encontrar
    todas las variables alcanzables así, A incluida.

    @param g: dict  Gramática con el formato de motor/gramatica.py.
    @return: dict[str, list[str]]  Variable -> lista de variables alcanzadas por unitarias.
    """
    prods = g["producciones"]
    pares = {}
    for a in g["variables"]:
        alcanzadas = [a]
        for b in alcanzadas:  # la lista crece mientras se recorre (BFS)
            for c in prods[b]:
                if len(c) == 1 and c[0] in prods and c[0] not in alcanzadas:
                    alcanzadas.append(c[0])
        pares[a] = alcanzadas
    return pares


def es_unitaria(cuerpo, g):
    """
    Indica si un cuerpo es una producción unitaria (A -> B con B variable).

    @param cuerpo: list[str]  Cuerpo de una producción.
    @param g: dict  Gramática con el formato de motor/gramatica.py.
    @return: bool  True si el cuerpo es un solo símbolo y ese símbolo es variable.
    """
    return len(cuerpo) == 1 and cuerpo[0] in g["producciones"]


def eliminar_unitarias(g):
    """
    Quita las producciones unitarias, reemplazando cada A -> B por las producciones no
    unitarias de todas las variables alcanzables desde A por cadenas de unitarias.

    @param g: dict  Gramática con el formato de motor/gramatica.py (ya sin ε).
    @return: dict  Gramática sin producciones unitarias.
    """
    pares = pares_unitarios(g)
    nuevas = {}
    for a in g["variables"]:
        lista = []
        for b in pares[a]:
            for c in g["producciones"][b]:
                if not es_unitaria(c, g) and c not in lista:
                    lista.append(c)
        nuevas[a] = lista
    return construir(g["inicial"], nuevas)


def generadores(g):
    """
    Calcula las variables generadoras (las que derivan alguna cadena de terminales).

    Repite vueltas agregando A si algún cuerpo de A usa solo símbolos generadores o
    terminales, hasta que una vuelta no agregue nada.

    @param g: dict  Gramática con el formato de motor/gramatica.py.
    @return: list[str]  Variables generadoras, en el orden de g["variables"].
    """
    prods = g["producciones"]
    gen = set()
    cambio = True
    while cambio:
        cambio = False
        for a, cuerpos in prods.items():
            if a not in gen and any(all(s in gen or s not in prods for s in c) for c in cuerpos):
                gen.add(a)
                cambio = True
    return [a for a in g["variables"] if a in gen]


def eliminar_no_generadores(g, acepta_vacio=False):
    """
    Quita las variables y producciones que no generan ninguna cadena de terminales.

    Si el símbolo inicial no genera nada, normalmente es un error (lenguaje vacío). La
    excepción es una gramática cuyo lenguaje es exactamente {ε}: ahí el inicial tampoco
    genera una cadena de terminales, pero `acepta_vacio=True` permite seguir y deja al
    inicial sin producciones en vez de lanzar el error.

    @param g: dict  Gramática con el formato de motor/gramatica.py (ya sin ε ni unitarias).
    @param acepta_vacio: bool  True si el símbolo inicial es anulable (el lenguaje puede
        ser exactamente {ε} en vez de vacío).
    @return: dict  Gramática sin símbolos no generadores.
    @raises ValueError: si el inicial no genera nada y `acepta_vacio` es False.
    """
    gen = set(generadores(g))
    vacio = g["inicial"] not in gen
    if vacio and not acepta_vacio:
        raise ValueError(
            f"El símbolo inicial {g['inicial']} no genera ninguna cadena: el lenguaje es vacío."
        )
    prods = g["producciones"]
    nuevas = {
        a: [c for c in cuerpos if all(s in gen or s not in prods for s in c)]
        for a, cuerpos in prods.items()
        if a in gen or (vacio and a == g["inicial"])
    }
    return construir(g["inicial"], nuevas)


def alcanzables(g):
    """
    Calcula las variables alcanzables desde el símbolo inicial.

    Hace un BFS desde el inicial siguiendo cualquier producción.

    @param g: dict  Gramática con el formato de motor/gramatica.py.
    @return: list[str]  Variables alcanzables, en el orden de g["variables"].
    """
    prods = g["producciones"]
    vistos = [g["inicial"]]
    for a in vistos:  # BFS sobre la lista que crece
        for c in prods[a]:
            for s in c:
                if s in prods and s not in vistos:
                    vistos.append(s)
    return [a for a in g["variables"] if a in vistos]


def eliminar_inalcanzables(g):
    """
    Quita las variables y producciones no alcanzables desde el símbolo inicial.

    @param g: dict  Gramática con el formato de motor/gramatica.py.
    @return: dict  Gramática sin símbolos inalcanzables.
    """
    alc = set(alcanzables(g))
    nuevas = {a: c for a, c in g["producciones"].items() if a in alc}
    return construir(g["inicial"], nuevas)


def _quitadas(antes, despues):
    """
    Lista las variables que estaban en `antes` y ya no están en `despues`.

    @param antes: dict  Gramática previa.
    @param despues: dict  Gramática posterior.
    @return: list[str]  Variables quitadas, en el orden de `antes`.
    """
    return [a for a in antes["variables"] if a not in despues["variables"]]


def simplificar(g):
    """
    Aplica las tres eliminaciones (ε, unitarias, inútiles) en orden.

    Si el símbolo inicial es anulable pero no genera ninguna cadena de terminales, el
    lenguaje es exactamente {ε}: la gramática resultante queda sin producciones en vez de
    lanzar el error de lenguaje vacío.

    @param g: dict  Gramática leída con motor/gramatica.py.
    @return: tuple[dict, list[dict]]  (gramatica_simplificada, pasos), cada paso con el
        formato de paso().
    @raises ValueError: si el lenguaje es vacío (el inicial no genera nada y no es
        anulable) o si un cuerpo excede MAX_ANULABLES_POR_CUERPO.
    """
    pasos = [paso("Gramática original", "Gramática leída del archivo, sin cambios.", g)]

    # 1. Producciones ε
    nulos = anulables(g)
    sin_e = eliminar_epsilon(g)
    detalle = f"Anulables: {_conjunto(nulos)}. "
    if nulos:
        detalle += (
            "Cada producción se reemplaza por todas sus variantes omitiendo anulables, "
            "y se descartan las producciones ε."
        )
    else:
        detalle += "No hay producciones ε; la gramática no cambia."
    if g["inicial"] in nulos:
        detalle += (
            f" Como {g['inicial']} es anulable, ε pertenece al lenguaje; se omite porque CYK"
            " solo evalúa oraciones no vacías."
        )
    pasos.append(paso("Eliminar producciones ε", detalle, sin_e))

    # 2. Producciones unitarias
    pares = pares_unitarios(sin_e)
    unitarios = [f"({a}, {b})" for a in sin_e["variables"] for b in pares[a] if b != a]
    sin_u = eliminar_unitarias(sin_e)
    if unitarios:
        detalle = (
            f"Pares unitarios: {', '.join(unitarios)}. Cada A -> B se reemplaza por las "
            "producciones no unitarias de B."
        )
    else:
        detalle = "No hay producciones unitarias; la gramática no cambia."
    pasos.append(paso("Eliminar producciones unitarias", detalle, sin_u))

    # 3a. No generadores
    gen = generadores(sin_u)
    vacio = g["inicial"] not in set(gen)
    sin_ng = eliminar_no_generadores(sin_u, acepta_vacio=(g["inicial"] in nulos))
    quitadas = _quitadas(sin_u, sin_ng)
    detalle = f"Generadores: {_conjunto(gen)}. "
    if vacio:
        detalle += (
            g["inicial"] + " no genera ninguna cadena de terminales, pero es anulable: "
            "el lenguaje es {ε} y la gramática queda sin producciones."
        )
    elif quitadas:
        detalle += f"Se eliminan {_conjunto(quitadas)} y las producciones que las usan."
    else:
        detalle += "Todas las variables generan alguna cadena."
    pasos.append(paso("Eliminar símbolos no generadores", detalle, sin_ng))

    # 3b. Inalcanzables
    alc = alcanzables(sin_ng)
    final = eliminar_inalcanzables(sin_ng)
    quitadas = _quitadas(sin_ng, final)
    detalle = f"Alcanzables desde {g['inicial']}: {_conjunto(alc)}. "
    detalle += (
        f"Se eliminan {_conjunto(quitadas)}." if quitadas else "Todas las variables son alcanzables."
    )
    pasos.append(paso("Eliminar símbolos inalcanzables", detalle, final))

    return final, pasos
