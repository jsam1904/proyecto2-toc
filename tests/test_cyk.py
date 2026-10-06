"""Tests de la Fase 2: tokenizador, CYK, parse tree y pipeline completo.

Ejecutar desde la raíz:  python -m unittest discover tests
"""

import itertools
import unittest
from pathlib import Path

from motor.arbol import construir, hojas
from motor.cyk import ejecutar_cyk, tokenizar
from motor.gramatica import leer_archivo
from motor.main import ejecutar, preparar

GRAMATICAS = Path(__file__).resolve().parent.parent / "gramaticas"
INGLES = (GRAMATICAS / "ingles.txt").read_text(encoding="utf-8")
EXPRESIONES = (GRAMATICAS / "1.txt").read_text(encoding="utf-8")

ACEPTADAS_INGLES = [
    "She eats a cake with a fork",
    "The cat drinks the beer",
    "she cooks",
    "he cuts the meat in the oven",
    "the dog eats the soup with a spoon in the oven",
    "the soup eats a knife",  # sintácticamente correcta aunque no tenga sentido
]
RECHAZADAS_INGLES = [
    "the cat",              # falta el verbo
    "she eats cake",        # falta el determinante
    "eats she",
    "she the cat",
    "a cat with a fork",
    "she eats a pizza",     # 'pizza' no está en el alfabeto
    "",
]


def acepta(texto, oracion):
    return ejecutar(texto, oracion)["cyk"]["acepta"]


class TestTokenizador(unittest.TestCase):
    def test_sin_espacios(self):
        terminales = ["id", "(", ")", "+", "*"]
        self.assertEqual(tokenizar("(id*id)+id", terminales), (["(", "id", "*", "id", ")", "+", "id"], None))

    def test_mayusculas(self):
        self.assertEqual(tokenizar("She EATS", ["she", "eats"]), (["she", "eats"], None))

    def test_simbolo_desconocido(self):
        tokens, error = tokenizar("id - id", ["id", "+"])
        self.assertIsNotNone(error)


class TestCYK(unittest.TestCase):
    def test_ingles(self):
        for o in ACEPTADAS_INGLES:
            with self.subTest(o=o):
                self.assertTrue(acepta(INGLES, o))
        for o in RECHAZADAS_INGLES:
            with self.subTest(o=o):
                self.assertFalse(acepta(INGLES, o))

    def test_expresiones(self):
        for o in ["(id*id)+id", "id", "id + id * id", "((id))", "id*(id+id)"]:
            with self.subTest(o=o):
                self.assertTrue(acepta(EXPRESIONES, o))
        for o in ["id+", "(id", "", "+id", "id id", "()"]:
            with self.subTest(o=o):
                self.assertFalse(acepta(EXPRESIONES, o))

    def test_epsilon_en_el_lenguaje(self):
        self.assertTrue(acepta("S -> a S b | e", ""))
        self.assertTrue(acepta("S -> a S b | e", "a a b b"))
        self.assertFalse(acepta("S -> a S b | e", "a b b"))

    def test_tiempo_y_ambiguedad(self):
        r = ejecutar("S -> S S | a", "a a a a")
        self.assertTrue(r["cyk"]["acepta"])
        self.assertGreaterEqual(r["cyk"]["tiempo_ms"], 0)
        self.assertEqual(r["cyk"]["num_arboles"], 5)  # número de Catalan C3

    def test_pasos_uno_por_celda(self):
        r = ejecutar(INGLES, "she eats a cake")
        n = r["cyk"]["n"]
        self.assertEqual(len(r["cyk"]["pasos"]), n * (n + 1) // 2)
        self.assertEqual(r["cyk"]["pasos"][-1]["resultado"], ["S"])

    def test_cnf_del_motor_decide_igual_que_1_cnf(self):
        """Para toda cadena de largo <= 6 sobre {id ( ) + *} ambas CNF deciden igual."""
        nuestra = preparar(EXPRESIONES)["cnf"]
        referencia = leer_archivo(GRAMATICAS / "1-cnf.txt")
        aceptadas = 0
        for n in range(1, 7):
            for w in itertools.product(["id", "(", ")", "+", "*"], repeat=n):
                a = ejecutar_cyk(nuestra, list(w))[0]["acepta"]
                b = ejecutar_cyk(referencia, list(w))[0]["acepta"]
                self.assertEqual(a, b, w)
                aceptadas += a
        self.assertGreaterEqual(aceptadas, 15)


class TestArbol(unittest.TestCase):
    def test_hojas_reproducen_la_oracion(self):
        prep = preparar(INGLES)
        tokens = "he cuts the meat in the oven".split()
        r, tabla = ejecutar_cyk(prep["cnf"], tokens)
        self.assertEqual(hojas(construir(prep["cnf"], tokens, tabla)), tokens)

    def test_arbol_sin_auxiliares(self):
        r = ejecutar(EXPRESIONES, "(id*id)+id")
        arbol = r["arbol"]
        self.assertEqual(arbol["auxiliares"], ["Z", "W", "V", "L", "R", "P", "M"])
        self.assertEqual(arbol["corchetes_simplificado"], "[E [T ( [E [F id] [Y * [F id]]] )] [X + [T id]]]")
        self.assertNotIn("Z", arbol["corchetes_simplificado"])

    def test_sin_arbol_si_se_rechaza(self):
        self.assertIsNone(ejecutar(INGLES, "the cat")["arbol"])


class TestBackend(unittest.TestCase):
    def setUp(self):
        try:
            from fastapi.testclient import TestClient
        except ImportError:  # httpx no instalado
            self.skipTest("fastapi[testclient] no disponible")
        from backend.app import app

        self.cliente = TestClient(app)

    def test_cyk(self):
        r = self.cliente.post("/cyk", json={"gramatica": INGLES, "oracion": "She eats a cake with a fork"})
        self.assertEqual(r.status_code, 200)
        datos = r.json()
        self.assertTrue(datos["cyk"]["acepta"])
        self.assertIn("pasos_cnf", datos)
        self.assertIsNotNone(datos["arbol"])

    def test_gramatica_invalida(self):
        r = self.cliente.post("/cyk", json={"gramatica": "S -> a | | b", "oracion": "a"})
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()
