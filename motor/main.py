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
    """
    Lectura + simplificación + CNF (Javier).

    @param texto: str  Texto de la gramática.
    @return: dict  gramatica, simplificacion, simplificada, cnf, pasos_cnf,
        epsilon_en_lenguaje, advertencias y tiempo_conversion_ms.
    @raises ValueError: si la gramática es inválida, excede un límite o su lenguaje es vacío.
    """
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
        "advertencias": g.get("advertencias", []),
        "tiempo_conversion_ms": (time.perf_counter() - inicio) * 1000,
    }


def analizar(prep, oracion):
    """
    Tokenización + CYK + árbol sobre una gramática ya preparada.

    @param prep: dict  Resultado de preparar().
    @param oracion: str  Oración a evaluar.
    @return: dict  {"oracion", "cyk", "arbol"}.
    @raises ValueError: si la oración excede un límite de motor/limites.py.
    """
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
    """
    Pipeline completo para el backend: todo lo de /gramatica + cyk + arbol.

    Si construir el árbol o contar los parse trees desborda la pila de recursión (una
    oración o gramática demasiado profunda), lo convierte en ValueError en vez de dejar
    que suba el RecursionError.

    @param texto: str  Texto de la gramática.
    @param oracion: str  Oración a evaluar.
    @return: dict  Todo lo de preparar() más oracion, cyk y arbol.
    @raises ValueError: si la gramática o la oración son inválidas, exceden un límite, o
        la recursión es demasiado profunda.
    """
    try:
        prep = preparar(texto)
        return {**prep, **analizar(prep, oracion)}
    except RecursionError:
        raise ValueError(
            "La oración es demasiado compleja para procesarla (recursión demasiado profunda); "
            "acórtala o simplifica la gramática."
        ) from None


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
    """
    Imprime el resultado de analizar() en consola: tokens, tabla, veredicto y parse tree.

    @param r: dict  Resultado de analizar() ({"oracion", "cyk", "arbol"}).
    @param solo_resultado: bool  Si es True, omite tokens y tabla.
    """
    cyk = r["cyk"]
    if cyk["error_tokens"]:
        print(f"Tokenización: {cyk['error_tokens']}")
    elif not solo_resultado:
        print("Tokens: " + " · ".join(cyk["tokens"]) if cyk["tokens"] else "Oración vacía (ε)")
        if cyk["n"]:
            _imprimir_tabla(cyk)
    print(f"\nResultado: {'SÍ' if cyk['acepta'] else 'NO'}   (CYK tardó {cyk['tiempo_ms']:.4f} ms)")
    if r["arbol"]:
        num = cyk["num_arboles"]  # puede venir como str si supera MAX_ENTERO_SEGURO_JS
        if isinstance(num, str) or num > 1:
            print(f"La oración es ambigua: {num} parse trees distintos (se muestra uno).")
        print("Parse tree (CNF):           " + r["arbol"]["corchetes_cnf"])
        print("Parse tree (sin auxiliares): " + r["arbol"]["corchetes_simplificado"])


def main():
    """Punto de entrada del CLI: parsea argumentos y corre el pipeline sobre el archivo
    y las oraciones dadas (o las pide por consola si no se dio ninguna)."""
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Simplifica una CFG, la pasa a CNF y decide w ∈ L(G) con CYK.")
    parser.add_argument("archivo", help="archivo .txt de la gramática")
    parser.add_argument("oraciones", nargs="*", help="oración(es) a evaluar; sin ninguna se piden por consola")
    parser.add_argument("--solo-resultado", action="store_true", help="solo SÍ/NO, tiempo y árbol")
    parser.add_argument("--json", action="store_true", help="imprime el JSON completo (primera oración)")
    args = parser.parse_args()

    try:
        with open(args.archivo, encoding="utf-8-sig") as f:
            texto = f.read()
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo '{args.archivo}'.")
        sys.exit(1)
    except IsADirectoryError:
        print(f"Error: '{args.archivo}' es un directorio, no un archivo.")
        sys.exit(1)
    except UnicodeDecodeError:
        print(f"Error: '{args.archivo}' no es un archivo de texto UTF-8 válido.")
        sys.exit(1)
    except OSError as e:
        print(f"Error al abrir '{args.archivo}': {e.strerror or e}.")
        sys.exit(1)

    try:
        if args.json:
            oracion = args.oraciones[0] if args.oraciones else ""
            print(json.dumps(ejecutar(texto, oracion), ensure_ascii=False, indent=2))
            return
        prep = preparar(texto)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if prep["advertencias"]:
        print("\nAdvertencias:")
        for a in prep["advertencias"]:
            print(f"  - {a}")

    if not args.solo_resultado:
        _titulo("Simplificación")
        _imprimir_pasos(prep["simplificacion"])
        _titulo("Forma Normal de Chomsky")
        _imprimir_pasos(prep["pasos_cnf"][1:])
        print(f"\nTiempo de simplificación + CNF: {prep['tiempo_conversion_ms']:.3f} ms")

    def evaluar(oracion):
        """Imprime el resultado de CYK para una oración; reporta errores sin interrumpir
        el programa (una oración inválida no debe tumbar las demás)."""
        _titulo(f'CYK: w = "{oracion}"')
        try:
            _imprimir_resultado(analizar(prep, oracion), args.solo_resultado)
        except ValueError as e:
            print(f"Error: {e}")

    if args.oraciones:
        for oracion in args.oraciones:
            evaluar(oracion)
        return
    print("\nEscribe una oración por línea (línea vacía o Ctrl+D para salir).")
    while True:
        try:
            oracion = input("w = ")
            if not oracion.strip():
                break
            evaluar(oracion)
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nSaliendo.")
            break


if __name__ == "__main__":
    main()
