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
    """
    Construye el parse tree de la oración completa.

    Baja recursivamente desde el símbolo inicial en la celda [0][n-1] siguiendo los
    backpointers de cyk.py: A -> B C (con su corte k) da dos hijos y A -> token da una
    hoja. Si la oración es ambigua, toma el primer árbol que encuentra.

    @param g: dict  Gramática en CNF.
    @param tokens: list[str]  Oración ya tokenizada.
    @param tabla: list[list[dict]]  Tabla devuelta por cyk.llenar_tabla.
    @return: dict | None  Nodo raíz ({"simbolo", "rango", "hijos", "hoja"}), o None si la
        oración no fue aceptada.
    """
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
    """
    Quita los nodos de variables auxiliares del árbol, subiendo sus hijos al padre.

    La raíz nunca es auxiliar (es el símbolo inicial de la gramática simplificada), así
    que siempre queda un solo árbol.

    @param nodo: dict  Raíz del árbol (nodo de construir()).
    @param auxiliares: set[str]  Variables que la CNF agregó y no deben aparecer.
    @return: dict  Árbol sin nodos auxiliares.
    """

    def visitar(n):
        if n["hoja"]:
            return [dict(n)]
        hijos = [h2 for h in n["hijos"] for h2 in visitar(h)]
        if n["simbolo"] in auxiliares:
            return hijos
        return [{"simbolo": n["simbolo"], "rango": n["rango"], "hijos": hijos, "hoja": False}]

    return visitar(nodo)[0]


def a_corchetes(nodo):
    """
    Convierte un árbol a notación con corchetes, p. ej. [S [NP she] [VP cooks]].

    @param nodo: dict  Raíz del árbol a convertir.
    @return: str  Texto en notación de corchetes.
    """
    if nodo["hoja"]:
        return nodo["simbolo"]
    return "[" + nodo["simbolo"] + " " + " ".join(a_corchetes(h) for h in nodo["hijos"]) + "]"


def a_grafo(raiz, auxiliares=()):
    """
    Convierte el árbol a nodos y aristas para dibujarlo con Cytoscape en el frontend.

    @param raiz: dict  Raíz del árbol a convertir.
    @param auxiliares: set[str]  Variables auxiliares de la CNF, para marcarlas con
        tipo "auxiliar" en vez de "variable".
    @return: dict  {"nodos": [...], "aristas": [...]}; cada nodo tiene id, label, tipo
        ("variable", "auxiliar" u "hoja") y rango.
    """
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
    """
    Lista los terminales del árbol de izquierda a derecha.

    @param nodo: dict  Raíz del árbol.
    @return: list[str]  Terminales en orden; debe coincidir con la oración tokenizada.
    """
    if nodo["hoja"]:
        return [nodo["simbolo"]]
    return [s for h in nodo["hijos"] for s in hojas(h)]


def describir(g_cnf, g_simple, tokens, tabla):
    """
    Arma todo lo que el frontend y el CLI necesitan del árbol.

    @param g_cnf: dict  Gramática en CNF (la que decidió CYK).
    @param g_simple: dict  Gramática simplificada, antes de la CNF (define qué variables
        son auxiliares: las que están en g_cnf pero no en g_simple).
    @param tokens: list[str]  Oración ya tokenizada.
    @param tabla: list[list[dict]]  Tabla devuelta por cyk.llenar_tabla.
    @return: dict | None  {"auxiliares", "cnf", "simplificado", "corchetes_cnf",
        "corchetes_simplificado"}, o None si la oración no fue aceptada.
    """
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
