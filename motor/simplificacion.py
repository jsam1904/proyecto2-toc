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


def paso(titulo, detalle, gramatica):
    return {
        "titulo": titulo,
        "detalle": detalle,
        "gramatica": gramatica,
        "texto": a_texto(gramatica, epsilon=EPSILON),
    }


def _conjunto(simbolos):
    return "{" + ", ".join(simbolos) + "}" if simbolos else "∅"


def anulables(g):
    """Variables que derivan ε, en orden de las variables de la gramática."""
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
    nulos = set(anulables(g))
    nuevas = {}
    for a, cuerpos in g["producciones"].items():
        lista = []
        for cuerpo in cuerpos:
            # Para cada anulable: conservarlo u omitirlo. product() da primero el cuerpo completo.
            opciones = [[(s,), ()] if s in nulos else [(s,)] for s in cuerpo]
            for eleccion in product(*opciones):
                variante = [s for parte in eleccion for s in parte]
                if variante and variante not in lista:
                    lista.append(variante)
        nuevas[a] = lista
    return construir(g["inicial"], nuevas)


def pares_unitarios(g):
    """Para cada variable A, las variables B tales que A =>* B solo con unitarias (A incluida)."""
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
    return len(cuerpo) == 1 and cuerpo[0] in g["producciones"]


def eliminar_unitarias(g):
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
    """Variables que derivan alguna cadena de terminales."""
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


def eliminar_no_generadores(g):
    gen = set(generadores(g))
    if g["inicial"] not in gen:
        raise ValueError(
            f"El símbolo inicial {g['inicial']} no genera ninguna cadena: el lenguaje es vacío."
        )
    prods = g["producciones"]
    nuevas = {
        a: [c for c in cuerpos if all(s in gen or s not in prods for s in c)]
        for a, cuerpos in prods.items()
        if a in gen
    }
    return construir(g["inicial"], nuevas)


def alcanzables(g):
    prods = g["producciones"]
    vistos = [g["inicial"]]
    for a in vistos:  # BFS sobre la lista que crece
        for c in prods[a]:
            for s in c:
                if s in prods and s not in vistos:
                    vistos.append(s)
    return [a for a in g["variables"] if a in vistos]


def eliminar_inalcanzables(g):
    alc = set(alcanzables(g))
    nuevas = {a: c for a, c in g["producciones"].items() if a in alc}
    return construir(g["inicial"], nuevas)


def _quitadas(antes, despues):
    return [a for a in antes["variables"] if a not in despues["variables"]]


def simplificar(g):
    """Aplica las tres eliminaciones y devuelve `(gramatica_simplificada, pasos)`."""
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
    sin_ng = eliminar_no_generadores(sin_u)
    quitadas = _quitadas(sin_u, sin_ng)
    detalle = f"Generadores: {_conjunto(gen)}. "
    detalle += (
        f"Se eliminan {_conjunto(quitadas)} y las producciones que las usan."
        if quitadas
        else "Todas las variables generan alguna cadena."
    )
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
