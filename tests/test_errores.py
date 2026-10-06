"""Tests de robustez: entradas que antes rompían la app (casos a-t de la tarea).

Ejecutar desde la raíz:  python -m unittest discover tests
"""

import subprocess
import sys
import unittest
from pathlib import Path

from motor.cyk import ejecutar_cyk, tokenizar
from motor.gramatica import leer_archivo, leer_texto
from motor.limites import MAX_CHARS_ORACION, MAX_TOKENS
from motor.main import ejecutar

RAIZ = Path(__file__).resolve().parent.parent
GRAMATICAS = RAIZ / "gramaticas"


class TestGramatica(unittest.TestCase):
    def test_a_lenguaje_epsilon_no_es_error(self):
        """a: 'S -> e' no lanza error; la CNF queda sin producciones."""
        r = ejecutar("S -> e", "")
        self.assertTrue(r["cyk"]["acepta"])
        self.assertEqual(r["cnf"]["producciones"], {"S": []})

    def test_a_lenguaje_epsilon_rechaza_otra_oracion(self):
        """a: con 'S -> e' cualquier oración no vacía se rechaza."""
        self.assertFalse(ejecutar("S -> e", "a")["cyk"]["acepta"])

    def test_a_lenguaje_vacio_de_verdad_sigue_dando_error(self):
        """a (ojo): si el inicial no genera nada y no es anulable, sigue siendo error."""
        with self.assertRaises(ValueError):
            ejecutar("S -> a S", "a")

    def test_b_doble_flecha_es_error(self):
        """b: 'S -> a -> b' lanza ValueError por tener más de una flecha."""
        with self.assertRaisesRegex(ValueError, "más de una flecha"):
            leer_texto("S -> a -> b")

    def test_c_epsilon_unicode_como_e(self):
        """c: 'ε' se trata igual que 'e' (debe ir sola en su alternativa)."""
        g = leer_texto("S -> a S | ε")
        self.assertEqual(g["producciones"]["S"], [["a", "S"], []])

    def test_c_epsilon_unicode_acompanada_es_error(self):
        """c: 'ε' junto a otro símbolo en la misma alternativa sigue siendo error."""
        with self.assertRaises(ValueError):
            leer_texto("S -> a ε")

    def test_d_bom_en_texto(self):
        """d: leer_texto descarta un BOM inicial antes de procesar la primera línea."""
        g = leer_texto("﻿S -> a")
        self.assertEqual(g["inicial"], "S")
        self.assertEqual(g["terminales"], ["a"])

    def test_d_bom_en_archivo(self):
        """d: leer_archivo abre con utf-8-sig, así que un archivo con BOM se lee igual."""
        tmp = RAIZ / "tests" / "_tmp_bom.txt"
        tmp.write_bytes("﻿S -> a".encode("utf-8-sig"))
        try:
            g = leer_archivo(tmp)
            self.assertEqual(g["inicial"], "S")
        finally:
            tmp.unlink()

    def test_e_cabeza_invalida_es_error(self):
        """e: una cabeza que no es un nombre válido ('(') lanza ValueError."""
        with self.assertRaisesRegex(ValueError, "nombre de variable válido"):
            leer_texto("( -> a")

    def test_e_cabeza_con_prima_es_valida(self):
        """e: una variable con prima (E') es un nombre válido."""
        g = leer_texto("E' -> a")
        self.assertEqual(g["inicial"], "E'")

    def test_f_comentario_despues_de_la_regla(self):
        """f: '#' inicia un comentario en cualquier parte de la línea."""
        g = leer_texto("S -> a # hola")
        self.assertEqual(g["producciones"], {"S": [["a"]]})

    def test_g_mayuscula_sin_reglas_no_es_error(self):
        """g: un símbolo con mayúscula sin reglas se trata como terminal, sin error."""
        g = leer_texto("S -> A b")
        self.assertIn("A", g["terminales"])

    def test_g_mayuscula_sin_reglas_genera_advertencia(self):
        """g: ese caso agrega una advertencia en el JSON."""
        g = leer_texto("S -> A b")
        self.assertIn("A no tiene producciones; se trata como terminal.", g["advertencias"])

    def test_h_explosion_de_anulables_es_error(self):
        """h: un cuerpo con más de MAX_ANULABLES_POR_CUERPO anulables lanza ValueError
        antes de llamar product(), en vez de colgar la app."""
        texto = "S -> " + " ".join(["A"] * 15) + "\nA -> a | e"
        with self.assertRaisesRegex(ValueError, "anulables"):
            ejecutar(texto, "a")


class TestOracion(unittest.TestCase):
    def test_i_max_tokens_es_error(self):
        """i: una oración con más de MAX_TOKENS tokens lanza ValueError claro."""
        with self.assertRaisesRegex(ValueError, f"el máximo es {MAX_TOKENS}"):
            tokenizar(" ".join(["a"] * (MAX_TOKENS + 1)), ["a"])

    def test_i_max_chars_oracion_es_error(self):
        """i: una oración con más caracteres que MAX_CHARS_ORACION lanza ValueError."""
        with self.assertRaises(ValueError):
            tokenizar("a" * (MAX_CHARS_ORACION + 1), ["a"])

    def test_j_tokenizador_con_retroceso(self):
        """j: el tokenizador retrocede si el prefijo más largo no deja partir el resto."""
        self.assertEqual(tokenizar("abc", ["a", "ab", "bc"]), (["a", "bc"], None))

    def test_j_prefiere_el_mas_largo_cuando_sí_alcanza(self):
        """j: sigue preferido el terminal más largo cuando no hace falta retroceder."""
        self.assertEqual(tokenizar("abc", ["a", "abc", "bc"]), (["abc"], None))

    def test_k_num_arboles_gigante_como_string(self):
        """k: si num_arboles > 2**53-1, se manda como string para no perder precisión en JS."""
        r = ejecutar("S -> S S | a", " ".join(["a"] * 40))
        self.assertIsInstance(r["cyk"]["num_arboles"], str)

    def test_k_num_arboles_normal_sigue_siendo_entero(self):
        """k: con pocos árboles, num_arboles sigue siendo un int normal."""
        r = ejecutar("S -> S S | a", "a a a a")
        self.assertIsInstance(r["cyk"]["num_arboles"], int)

    def test_l_recursion_profunda_se_convierte_en_valueerror(self):
        """l: un RecursionError durante el pipeline se convierte en ValueError, no se
        deja escapar (se simula directamente para no depender de la profundidad real
        de pila del entorno donde corran los tests)."""
        import motor.main as main_modulo

        original = main_modulo.analizar

        def explota(*a, **k):
            raise RecursionError("simulado")

        main_modulo.analizar = explota
        try:
            with self.assertRaises(ValueError):
                main_modulo.ejecutar("S -> a", "a")
        finally:
            main_modulo.analizar = original


class TestBackend(unittest.TestCase):
    def setUp(self):
        try:
            from fastapi.testclient import TestClient
        except ImportError:  # httpx no instalado
            self.skipTest("fastapi[testclient] no disponible")
        from backend.app import app

        self.cliente = TestClient(app)

    def test_m_oracion_es_opcional(self):
        """m: Peticion.oracion tiene valor por defecto "" (POST /cyk sin oracion)."""
        r = self.cliente.post("/cyk", json={"gramatica": "S -> a"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["cyk"]["tokens"], [])

    def test_m_oracion_demasiado_larga_es_422(self):
        """m: una oración más larga que MAX_CHARS_ORACION se rechaza por validación (422)."""
        r = self.cliente.post("/cyk", json={"gramatica": "S -> a", "oracion": "a" * (MAX_CHARS_ORACION + 1)})
        self.assertEqual(r.status_code, 422)

    def test_n_error_inesperado_da_500_sin_traceback(self):
        """n: un error no previsto responde 500 con detail genérico, sin traceback."""
        from fastapi.testclient import TestClient

        import backend.app as app_modulo

        original = app_modulo.ejecutar
        app_modulo.ejecutar = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
        try:
            cliente = TestClient(app_modulo.app, raise_server_exceptions=False)
            r = cliente.post("/cyk", json={"gramatica": "S -> a", "oracion": "a"})
            self.assertEqual(r.status_code, 500)
            self.assertEqual(r.json(), {"detail": "Error interno del motor"})
        finally:
            app_modulo.ejecutar = original


class TestCLI(unittest.TestCase):
    def _correr(self, *args, entrada=None):
        return subprocess.run(
            [sys.executable, "-m", "motor.main", *args],
            cwd=RAIZ,
            input=entrada,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_s_archivo_inexistente_sin_traceback(self):
        """s: un archivo inexistente termina con exit 1 y un mensaje claro, sin traceback."""
        r = self._correr("gramaticas/no-existe.txt", "a")
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("no se encontró", r.stdout)

    def test_s_ruta_es_carpeta_sin_traceback(self):
        """s: pasar una carpeta en vez de un archivo termina con exit 1, sin traceback."""
        r = self._correr("gramaticas", "a")
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("Traceback", r.stderr)

    def test_t_eof_en_modo_interactivo_sale_limpio(self):
        """t: Ctrl+D (stdin vacío) en el modo interactivo termina sin error ni traceback."""
        r = self._correr("gramaticas/1.txt", entrada="")
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("Traceback", r.stderr)


if __name__ == "__main__":
    unittest.main()
