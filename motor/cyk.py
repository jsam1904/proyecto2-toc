"""Tokenizador de la oración + algoritmo CYK + medición de tiempo.

Responsable: Angel.

Recibe la gramática en CNF (el dict de gramatica.py que devuelve cnf.a_cnf) y una
oración, y decide si la oración pertenece al lenguaje usando programación dinámica.

tabla[i][j] guarda, para la subcadena w[i..j] (inclusive), un dict
    variable -> lista de "backpointers"
donde cada backpointer es:
    ("t", token)    si viene de A -> token                         (longitud 1)
    (k, B, C)       si viene de A -> B C, con B en tabla[i][k] y C en tabla[k+1][j]
Guardar backpointers en lugar de solo un booleano es lo que permite construir el parse
tree (arbol.py) sin volver a correr el algoritmo.

Complejidad: O(n^3 · |R|), con n = número de tokens y |R| = número de reglas binarias.
Solo se cronometra el llenado de la tabla y la decisión (time.perf_counter); la
tokenización y los pasos para el frontend quedan fuera de la medición.
"""

import time

from motor.limites import MAX_CHARS_ORACION, MAX_ENTERO_SEGURO_JS, MAX_TOKENS


# ---------------------------------------------------------------------------
# Tokenización
# ---------------------------------------------------------------------------

def tokenizar(oracion, terminales):
    """
    Parte la oración en terminales de la gramática.

    1. Se separa por espacios.
    2. Si un trozo completo es terminal, es un token ("cake").
    3. Si no, se parte contra los terminales con retroceso (backtracking): en cada
       posición prueba primero el terminal más largo que calce, pero si ese camino no
       llega a partir el trozo completo, retrocede y prueba el siguiente más largo. Así
       "abc" con terminales {a, ab, bc} da ["a", "bc"] en vez de fallar tras tomar "ab".
    Si un trozo no coincide tal cual, se intenta en minúsculas ("She" -> "she").

    @param oracion: str  Oración a tokenizar.
    @param terminales: list[str]  Terminales de la gramática (en CNF).
    @return: tuple[list[str], str | None]  (tokens, error); error es None si se pudo
        tokenizar toda la oración.
    @raises ValueError: si la oración excede MAX_CHARS_ORACION caracteres o produce más
        de MAX_TOKENS tokens.
    """
    if len(oracion) > MAX_CHARS_ORACION:
        raise ValueError(f"La oración tiene {len(oracion)} caracteres; el máximo es {MAX_CHARS_ORACION}.")
    terminales = set(terminales)
    largos = sorted(terminales, key=len, reverse=True)
    tokens = []

    def partir(trozo):
        memo = {}
        progreso = 0

        def ir(i):
            nonlocal progreso
            progreso = max(progreso, i)
            if i == len(trozo):
                return []
            if i in memo:
                return memo[i]
            for t in largos:
                if t and trozo.startswith(t, i):
                    resto = ir(i + len(t))
                    if resto is not None:
                        memo[i] = [t] + resto
                        return memo[i]
            memo[i] = None
            return None

        resultado = ir(0)
        if resultado is None:
            return None, trozo[progreso:]
        return resultado, None

    for trozo in oracion.split():
        if trozo in terminales:
            tokens.append(trozo)
            continue
        if trozo.lower() in terminales:
            tokens.append(trozo.lower())
            continue
        partes, _ = partir(trozo)
        if partes is None:
            partes, resto = partir(trozo.lower())
            if partes is None:
                return tokens, f"'{resto}' no pertenece al alfabeto de la gramática"
        tokens.extend(partes)
    if len(tokens) > MAX_TOKENS:
        raise ValueError(f"la oración tiene {len(tokens)} tokens; el máximo es {MAX_TOKENS}")
    return tokens, None


# ---------------------------------------------------------------------------
# CYK
# ---------------------------------------------------------------------------

def _indices(g):
    """
    Construye índices para buscar rápido las reglas aplicables durante CYK.

    @param g: dict  Gramática en CNF.
    @return: tuple[dict, dict]  (por_terminal, por_par): terminal -> [A] para A -> t, y
        (B, C) -> [A] para A -> B C.
    """
    por_terminal = {}
    por_par = {}
    for a, cuerpos in g["producciones"].items():
        for c in cuerpos:
            if len(c) == 1:
                por_terminal.setdefault(c[0], []).append(a)
            elif len(c) == 2:
                por_par.setdefault((c[0], c[1]), []).append(a)
    return por_terminal, por_par


def llenar_tabla(g, tokens):
    """
    Núcleo del algoritmo: llena la tabla por largo de subcadena (1, 2, ..., n).

    @param g: dict  Gramática en CNF.
    @param tokens: list[str]  Oración ya tokenizada.
    @return: list[list[dict]]  Tabla n×n; tabla[i][j] es {variable: [backpointers]} para
        la subcadena tokens[i..j].
    """
    n = len(tokens)
    por_terminal, por_par = _indices(g)
    tabla = [[None] * n for _ in range(n)]

    # Largo 1: A -> token
    for i, tok in enumerate(tokens):
        celda = {}
        for a in por_terminal.get(tok, ()):
            celda.setdefault(a, []).append(("t", tok))
        tabla[i][i] = celda

    # Largo 2..n: para cada corte k, combinar tabla[i][k] × tabla[k+1][j] con A -> B C
    for largo in range(2, n + 1):
        for i in range(0, n - largo + 1):
            j = i + largo - 1
            celda = {}
            for k in range(i, j):
                izq = tabla[i][k]
                der = tabla[k + 1][j]
                if not izq or not der:
                    continue
                for b in izq:
                    for c in der:
                        for a in por_par.get((b, c), ()):
                            celda.setdefault(a, []).append((k, b, c))
            tabla[i][j] = celda
    return tabla


def ejecutar_cyk(g, tokens, epsilon_en_lenguaje=False):
    """
    Corre CYK sobre `tokens` y devuelve (resultado, tabla_con_backpointers).

    Si `num_arboles` supera MAX_ENTERO_SEGURO_JS (el entero más grande que JavaScript
    representa exacto), se manda como string en vez de number para que el frontend no
    pierda precisión al parsear el JSON.

    @param g: dict  Gramática en CNF.
    @param tokens: list[str]  Oración ya tokenizada.
    @param epsilon_en_lenguaje: bool  True si ε pertenece al lenguaje original (se usa
        solo cuando `tokens` está vacía).
    @return: tuple[dict, list[list[dict]]]  (resultado, tabla); resultado tiene las
        llaves tokens, n, acepta, tiempo_ms, tabla, pasos y num_arboles.
    """
    n = len(tokens)
    inicio = time.perf_counter()
    if n == 0:
        tabla = []
        acepta = epsilon_en_lenguaje
    else:
        tabla = llenar_tabla(g, tokens)
        acepta = g["inicial"] in tabla[0][n - 1]
    tiempo_ms = (time.perf_counter() - inicio) * 1000

    if not acepta:
        num_arboles = 0
    elif n == 0:
        num_arboles = 1
    else:
        num_arboles = contar_arboles(g, tabla)
    if num_arboles > MAX_ENTERO_SEGURO_JS:
        num_arboles = str(num_arboles)

    resultado = {
        "tokens": tokens,
        "n": n,
        "acepta": acepta,
        "tiempo_ms": tiempo_ms,
        "tabla": [[_ordenar(g, tabla[i][j]) if j >= i else None for j in range(n)] for i in range(n)],
        "pasos": pasos_de_tabla(g, tokens, tabla),
        "num_arboles": num_arboles,
    }
    return resultado, tabla


def _ordenar(g, celda):
    """
    Ordena las variables de una celda como aparecen en la gramática (se lee mejor que
    alfabético).

    @param g: dict  Gramática en CNF.
    @param celda: dict  {variable: [backpointers]} de una celda de la tabla.
    @return: list[str]  Variables de la celda, en el orden de g["variables"].
    """
    orden = {v: i for i, v in enumerate(g["variables"])}
    return sorted(celda, key=lambda v: orden.get(v, len(orden)))


def pasos_de_tabla(g, tokens, tabla):
    """
    Arma un paso por celda, en el orden en que CYK las llena, con las particiones
    probadas y las reglas que aplicaron.

    Se reconstruye desde los backpointers que dejó llenar_tabla, sin volver a correr CYK.

    @param g: dict  Gramática en CNF.
    @param tokens: list[str]  Oración ya tokenizada.
    @param tabla: list[list[dict]]  Tabla devuelta por llenar_tabla.
    @return: list[dict]  Un dict por celda, con su tipo ("terminal" o "combinacion").
    """
    n = len(tokens)
    pasos = []
    for largo in range(1, n + 1):
        for i in range(0, n - largo + 1):
            j = i + largo - 1
            celda = tabla[i][j]
            if largo == 1:
                pasos.append({
                    "i": i, "j": j, "largo": 1, "tipo": "terminal", "token": tokens[i],
                    "reglas": [f"{a} -> {tokens[i]}" for a in _ordenar(g, celda)],
                    "resultado": _ordenar(g, celda),
                })
                continue
            particiones = []
            for k in range(i, j):
                reglas = []
                for a in _ordenar(g, celda):
                    for bp in celda[a]:
                        if bp[0] == k:
                            regla = f"{a} -> {bp[1]} {bp[2]}"
                            if regla not in reglas:
                                reglas.append(regla)
                particiones.append({
                    "k": k,
                    "izquierda": [i, k],
                    "derecha": [k + 1, j],
                    "vars_izquierda": _ordenar(g, tabla[i][k]),
                    "vars_derecha": _ordenar(g, tabla[k + 1][j]),
                    "reglas": reglas,
                })
            pasos.append({
                "i": i, "j": j, "largo": largo, "tipo": "combinacion",
                "particiones": particiones, "resultado": _ordenar(g, celda),
            })
    return pasos


def contar_arboles(g, tabla):
    """
    Cuenta los parse trees distintos de la oración completa.

    Recorre los backpointers de forma recursiva con memoización: el número de árboles de
    una celda con A -> B C es el producto de los árboles de cada hijo, sumado sobre todas
    las reglas y particiones que llevan a A en esa celda.

    @param g: dict  Gramática en CNF.
    @param tabla: list[list[dict]]  Tabla devuelta por llenar_tabla.
    @return: int  Número de parse trees distintos (> 1 significa que la oración es ambigua).
    """
    n = len(tabla)
    memo = {}

    def cuenta(i, j, a):
        clave = (i, j, a)
        if clave not in memo:
            total = 0
            for bp in tabla[i][j].get(a, ()):
                if bp[0] == "t":
                    total += 1
                else:
                    k, b, c = bp
                    total += cuenta(i, k, b) * cuenta(k + 1, j, c)
            memo[clave] = total
        return memo[clave]

    return cuenta(0, n - 1, g["inicial"])
