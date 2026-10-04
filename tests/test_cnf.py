"""Tests de la Fase 1: lector, simplificación y CNF.

Ejecutar desde la raíz:  python -m unittest discover tests
"""

import unittest
from pathlib import Path

from motor.cnf import a_cnf, es_cnf
from motor.gramatica import a_texto, leer_archivo, leer_texto
from motor.simplificacion import simplificar

GRAMATICAS = Path(__file__).resolve().parent.parent / "gramaticas"


def cadenas(g, n):
    """Todas las cadenas de longitud <= n que genera g (punto fijo acotado; sirve con ε y unitarias)."""
    prods = g["producciones"]
    lenguaje = {a: set() for a in prods}

    def de_simbolo(s):
        return lenguaje[s] if s in prods else {(s,)}

    cambio = True
    while cambio:
        cambio = False
        for a, cuerpos in prods.items():
            for c in cuerpos:
                parciales = {()}
                for s in c:
                    parciales = {x + y for x in parciales for y in de_simbolo(s) if len(x) + len(y) <= n}
                nuevas = parciales - lenguaje[a]
                if nuevas:
                    lenguaje[a] |= nuevas
                    cambio = True
    return lenguaje[g["inicial"]]


def pipeline(ruta):
    g = leer_archivo(ruta)
    simple, _ = simplificar(g)
    cnf, _ = a_cnf(simple)
    return g, cnf


class TestLector(unittest.TestCase):
    def test_lee_1_txt(self):
        g = leer_archivo(GRAMATICAS / "1.txt")
        self.assertEqual(g["inicial"], "E")
        self.assertEqual(g["variables"], ["E", "X", "T", "Y", "F"])
        self.assertEqual(g["terminales"], ["+", "*", "(", ")", "id"])
        self.assertEqual(g["producciones"]["X"], [["+", "T", "X"], []])  # e -> ε = []
        self.assertEqual(g["producciones"]["F"], [["(", "E", ")"], ["id"]])

    def test_junta_lineas_de_la_misma_variable(self):
        g = leer_archivo(GRAMATICAS / "ingles.txt")
        self.assertEqual(g["inicial"], "S")
        self.assertEqual(len(g["producciones"]["VP"]), 6)
        self.assertEqual(len(g["producciones"]["N"]), 11)
        self.assertIn("Det", g["variables"])
        self.assertNotIn("Det", g["terminales"])

    def test_flecha_unicode_y_comentarios(self):
        g = leer_texto("# comentario\n\nS → a S b | e\n")
        self.assertEqual(g["producciones"], {"S": [["a", "S", "b"], []]})

    def test_ida_y_vuelta_a_texto(self):
        texto = (GRAMATICAS / "1.txt").read_text(encoding="utf-8")
        self.assertEqual(a_texto(leer_texto(texto)), texto.strip())

    def test_errores(self):
        for malo in ["", "S a b", "-> a", "S T -> a", "S -> a | | b", "S -> a e", "e -> a"]:
            with self.subTest(malo=malo), self.assertRaises(ValueError):
                leer_texto(malo)


class TestSimplificacion(unittest.TestCase):
    def test_1_txt_sin_epsilon_ni_unitarias(self):
        g, _ = simplificar(leer_archivo(GRAMATICAS / "1.txt"))
        for a, cuerpos in g["producciones"].items():
            for c in cuerpos:
                self.assertTrue(c, f"{a} conserva una producción ε")
                self.assertFalse(len(c) == 1 and c[0] in g["producciones"], f"{a} -> {c} es unitaria")
        self.assertEqual(
            a_texto(g),
            "E -> T X | F Y | ( E ) | id\n"
            "X -> + T X | + T\n"
            "T -> F Y | ( E ) | id\n"
            "Y -> * F Y | * F\n"
            "F -> ( E ) | id",
        )

    def test_elimina_inutiles(self):
        g, _ = simplificar(leer_texto("S -> A B | a\nA -> a A\nB -> b\nC -> c"))
        # A no genera nada -> se va S -> A B; luego B y C quedan inalcanzables.
        self.assertEqual(a_texto(g), "S -> a")

    def test_variable_solo_epsilon(self):
        g, _ = simplificar(leer_texto("S -> a A b\nA -> e"))
        self.assertEqual(a_texto(g), "S -> a b")

    def test_ciclo_de_unitarias(self):
        g, _ = simplificar(leer_texto("S -> A | a\nA -> S | b"))
        self.assertEqual(a_texto(g), "S -> a | b")

    def test_lenguaje_vacio(self):
        with self.assertRaises(ValueError):
            simplificar(leer_texto("S -> a S"))

    def test_pasos(self):
        _, pasos = simplificar(leer_archivo(GRAMATICAS / "1.txt"))
        self.assertEqual(len(pasos), 5)
        for p in pasos:
            self.assertEqual(set(p), {"titulo", "detalle", "gramatica", "texto"})
        self.assertIn("{X, Y}", pasos[1]["detalle"])


class TestCNF(unittest.TestCase):
    def test_1_txt_equivale_a_1_cnf(self):
        _, cnf = pipeline(GRAMATICAS / "1.txt")
        referencia = leer_archivo(GRAMATICAS / "1-cnf.txt")
        self.assertTrue(es_cnf(cnf))
        self.assertTrue(es_cnf(referencia))
        self.assertEqual(cadenas(cnf, 9), cadenas(referencia, 9))

    def test_1_txt_da_exactamente_1_cnf(self):
        _, cnf = pipeline(GRAMATICAS / "1.txt")
        referencia = (GRAMATICAS / "1-cnf.txt").read_text(encoding="utf-8")
        self.assertEqual(a_texto(cnf), a_texto(leer_texto(referencia)))

    def test_conserva_el_lenguaje_de_1_txt(self):
        original, cnf = pipeline(GRAMATICAS / "1.txt")
        self.assertEqual(cadenas(original, 9) - {()}, cadenas(cnf, 9))

    def test_ingles_queda_intacta(self):
        original, cnf = pipeline(GRAMATICAS / "ingles.txt")
        self.assertTrue(es_cnf(original))
        self.assertEqual(cnf, original)

    def test_cuerpos_largos_y_terminales(self):
        g, _ = simplificar(leer_texto("S -> a S b c | a b c"))
        cnf, pasos = a_cnf(g)
        self.assertTrue(es_cnf(cnf))
        self.assertEqual(cadenas(cnf, 9), cadenas(g, 9))
        self.assertEqual(pasos[-1]["titulo"], "Forma Normal de Chomsky")

    def test_rechaza_gramatica_sin_simplificar(self):
        with self.assertRaises(ValueError):
            a_cnf(leer_archivo(GRAMATICAS / "1.txt"))


if __name__ == "__main__":
    unittest.main()
