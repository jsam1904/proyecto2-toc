"""Límites del motor: constantes que evitan entradas que cuelguen o desborden la app."""

MAX_LINEAS = 200  # líneas máximas de un archivo de gramática
MAX_SIMBOLOS_POR_CUERPO = 20  # símbolos máximos en el cuerpo de una producción
MAX_CHARS_GRAMATICA = 20000  # caracteres máximos del texto de una gramática
MAX_ANULABLES_POR_CUERPO = 10  # anulables máximos en un cuerpo antes de generar sus variantes (evita 2^m)
MAX_TOKENS = 60  # tokens máximos de una oración (CYK es O(n^3))
MAX_CHARS_ORACION = 1000  # caracteres máximos de una oración antes de tokenizarla
MAX_ENTERO_SEGURO_JS = 2 ** 53 - 1  # mayor entero exacto en JavaScript (Number.MAX_SAFE_INTEGER)
