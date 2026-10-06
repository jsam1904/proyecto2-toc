"""Construcción del parse tree a partir de la tabla CYK.

Responsable: Angel.

Se arranca en el símbolo inicial de la celda [0][n-1] y se baja recursivamente por los
backpointers que guardó cyk.py: A -> B C (con su corte k) da dos hijos y A -> token da
una hoja. Si la oración es ambigua se toma el primer árbol encontrado; el total de
árboles lo da cyk.contar_arboles.

El árbol de la CNF incluye las variables auxiliares que agregó cnf.py (las de los
terminales como L, R, P, M y las de las colas como Z, W, V). `colapsar` las quita
subiendo sus hijos al padre, así el árbol se lee con las variables de la gramática
simplificada.

Nodo: {"simbolo", "rango": [i, j], "hijos": [...], "hoja": bool}
"""


def construir(g, tokens, tabla):
    """Parse tree de la oración completa, o None si no fue aceptada."""
    n = len(tokens)
    if n == 0 or g["inicial"] not in tabla[0][n - 1]:
        return None

    def bajar(i, j, a):
        bp = tabla[i][j][a][0]
        if bp[0] == "t":
            hoja = {"simbolo": bp[1], "rango": [i, j], "hijos": [], "hoja": True}
            return {"simbolo": a, "rango": [i, j], "hijos": [hoja], "hoja": False}
        k, b, c = bp
        return {"simbolo": a, "rango": [i, j], "hijos": [bajar(i, k, b), bajar(k + 1, j, c)], "hoja": False}

    return bajar(0, n - 1, g["inicial"])


def colapsar(nodo, auxiliares):
    """Quita los nodos de variables auxiliares subiendo sus hijos. La raíz nunca es
    auxiliar (es el símbolo inicial), así que siempre queda un solo árbol."""

    def visitar(n):
        if n["hoja"]:
            return [dict(n)]
        hijos = [h2 for h in n["hijos"] for h2 in visitar(h)]
        if n["simbolo"] in auxiliares:
            return hijos
        return [{"simbolo": n["simbolo"], "rango": n["rango"], "hijos": hijos, "hoja": False}]

    return visitar(nodo)[0]


def a_corchetes(nodo):
    """Notación con corchetes: [S [NP she] [VP cooks]]."""
    if nodo["hoja"]:
        return nodo["simbolo"]
    return "[" + nodo["simbolo"] + " " + " ".join(a_corchetes(h) for h in nodo["hijos"]) + "]"


def a_grafo(raiz, auxiliares=()):
    """Nodos y aristas para Cytoscape. tipo: "variable", "auxiliar" u "hoja"."""
    nodos, aristas = [], []

    def visitar(n, padre):
        nid = f"n{len(nodos)}"
        tipo = "hoja" if n["hoja"] else ("auxiliar" if n["simbolo"] in auxiliares else "variable")
        nodos.append({"id": nid, "label": n["simbolo"], "tipo": tipo, "rango": n["rango"]})
        if padre is not None:
            aristas.append({"id": f"e{nid}", "de": padre, "a": nid})
        for h in n["hijos"]:
            visitar(h, nid)

    visitar(raiz, None)
    return {"nodos": nodos, "aristas": aristas}


def hojas(nodo):
    """Terminales del árbol de izquierda a derecha (debe ser la oración tokenizada)."""
    if nodo["hoja"]:
        return [nodo["simbolo"]]
    return [s for h in nodo["hijos"] for s in hojas(h)]


def describir(g_cnf, g_simple, tokens, tabla):
    """Todo lo que el frontend y el CLI necesitan del árbol, o None si no hay árbol."""
    raiz = construir(g_cnf, tokens, tabla)
    if raiz is None:
        return None
    auxiliares = [v for v in g_cnf["variables"] if v not in g_simple["producciones"]]
    simple = colapsar(raiz, set(auxiliares))
    return {
        "auxiliares": auxiliares,
        "cnf": a_grafo(raiz, set(auxiliares)),
        "simplificado": a_grafo(simple),
        "corchetes_cnf": a_corchetes(raiz),
        "corchetes_simplificado": a_corchetes(simple),
    }
