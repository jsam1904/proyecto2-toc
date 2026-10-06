"""CLI que ejecuta el pipeline completo.

Responsable: Angel.

    lectura (gramatica.py) -> simplificación (simplificacion.py) -> CNF (cnf.py)
    -> tokenización + CYK (cyk.py) -> parse tree (arbol.py)

Uso, desde la raíz del proyecto:

    python -m motor.main gramaticas/ingles.txt "She eats a cake with a fork"
    python -m motor.main gramaticas/1.txt "(id*id)+id" "id+"
    python -m motor.main gramaticas/ingles.txt                 # pide oraciones por consola
    python -m motor.main gramaticas/ingles.txt "he cooks" --solo-resultado
    python -m motor.main gramaticas/ingles.txt "he cooks" --json

`ejecutar(texto, oracion)` es lo mismo que usa el backend en POST /cyk.
"""

import argparse
import json
import sys
import time

from motor.cnf import a_cnf
from motor.cyk import ejecutar_cyk, tokenizar
from motor.arbol import describir
from motor.gramatica import a_texto, leer_texto
from motor.simplificacion import anulables, simplificar


def preparar(texto):
    """Lectura + simplificación + CNF (Javier). Lanza ValueError si la gramática es
    inválida o su lenguaje es vacío."""
    inicio = time.perf_counter()
    g = leer_texto(texto)
    simple, pasos_simplificacion = simplificar(g)
    cnf, pasos_cnf = a_cnf(simple)
    return {
        "gramatica": g,
        "simplificacion": pasos_simplificacion,
        "simplificada": simple,
        "cnf": cnf,
        "pasos_cnf": pasos_cnf,
        "epsilon_en_lenguaje": g["inicial"] in anulables(g),
        "tiempo_conversion_ms": (time.perf_counter() - inicio) * 1000,
    }


def analizar(prep, oracion):
    """Tokenización + CYK + árbol sobre una gramática ya preparada."""
    cnf = prep["cnf"]
    tokens, error = tokenizar(oracion, cnf["terminales"])
    if error:
        cyk = {"tokens": tokens, "n": len(tokens), "acepta": False, "tiempo_ms": 0.0,
               "tabla": [], "pasos": [], "num_arboles": 0, "error_tokens": error}
        return {"oracion": oracion, "cyk": cyk, "arbol": None}
    cyk, tabla = ejecutar_cyk(cnf, tokens, prep["epsilon_en_lenguaje"])
    cyk["error_tokens"] = None
    arbol = describir(cnf, prep["simplificada"], tokens, tabla) if cyk["acepta"] and tokens else None
    return {"oracion": oracion, "cyk": cyk, "arbol": arbol}


def ejecutar(texto, oracion):
    """Pipeline completo para el backend: todo lo de /gramatica + cyk + arbol."""
    prep = preparar(texto)
    return {**prep, **analizar(prep, oracion)}


# ---------------------------------------------------------------------------
# Salida en consola
# ---------------------------------------------------------------------------

def _titulo(texto):
    linea = "=" * 70
    print(f"\n{linea}\n{texto}\n{linea}")


def _imprimir_pasos(pasos):
    for p in pasos:
        print(f"\n--- {p['titulo']} ---")
        print(p["detalle"])
        for linea in p["texto"].splitlines():
            print("  " + linea)


def _imprimir_tabla(cyk):
    n = cyk["n"]
    celdas = [" ".join(cyk["tabla"][i][j]) or "∅" for i in range(n) for j in range(i, n)]
    ancho = min(22, max(8, max(len(c) for c in celdas) + 2))
    print("\nTabla CYK (fila = largo de la subcadena, columna = posición donde empieza):")
    for largo in range(n, 0, -1):
        fila = ""
        for i in range(0, n - largo + 1):
            celda = " ".join(cyk["tabla"][i][i + largo - 1]) or "∅"
            fila += celda[: ancho - 1].ljust(ancho)
        print(f"  {largo:>2} | {fila}")
    print("     + " + "".join(t[: ancho - 1].ljust(ancho) for t in cyk["tokens"]))


def _imprimir_resultado(r, solo_resultado):
    cyk = r["cyk"]
    if cyk["error_tokens"]:
        print(f"Tokenización: {cyk['error_tokens']}")
    elif not solo_resultado:
        print("Tokens: " + " · ".join(cyk["tokens"]) if cyk["tokens"] else "Oración vacía (ε)")
        if cyk["n"]:
            _imprimir_tabla(cyk)
    print(f"\nResultado: {'SÍ' if cyk['acepta'] else 'NO'}   (CYK tardó {cyk['tiempo_ms']:.4f} ms)")
    if r["arbol"]:
        if cyk["num_arboles"] > 1:
            print(f"La oración es ambigua: {cyk['num_arboles']} parse trees distintos (se muestra uno).")
        print("Parse tree (CNF):           " + r["arbol"]["corchetes_cnf"])
        print("Parse tree (sin auxiliares): " + r["arbol"]["corchetes_simplificado"])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Simplifica una CFG, la pasa a CNF y decide w ∈ L(G) con CYK.")
    parser.add_argument("archivo", help="archivo .txt de la gramática")
    parser.add_argument("oraciones", nargs="*", help="oración(es) a evaluar; sin ninguna se piden por consola")
    parser.add_argument("--solo-resultado", action="store_true", help="solo SÍ/NO, tiempo y árbol")
    parser.add_argument("--json", action="store_true", help="imprime el JSON completo (primera oración)")
    args = parser.parse_args()

    with open(args.archivo, encoding="utf-8") as f:
        texto = f.read()
    try:
        if args.json:
            oracion = args.oraciones[0] if args.oraciones else ""
            print(json.dumps(ejecutar(texto, oracion), ensure_ascii=False, indent=2))
            return
        prep = preparar(texto)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if not args.solo_resultado:
        _titulo("Simplificación")
        _imprimir_pasos(prep["simplificacion"])
        _titulo("Forma Normal de Chomsky")
        _imprimir_pasos(prep["pasos_cnf"][1:])
        print(f"\nTiempo de simplificación + CNF: {prep['tiempo_conversion_ms']:.3f} ms")

    def evaluar(oracion):
        _titulo(f'CYK: w = "{oracion}"')
        _imprimir_resultado(analizar(prep, oracion), args.solo_resultado)

    if args.oraciones:
        for oracion in args.oraciones:
            evaluar(oracion)
        return
    print("\nEscribe una oración por línea (línea vacía o Ctrl+D para salir).")
    while True:
        try:
            oracion = input("w = ")
        except EOFError:
            break
        if not oracion.strip():
            break
        evaluar(oracion)


if __name__ == "__main__":
    main()
