# proyecto2-toc

Teoría de la Computación · Proyecto No. 2 · Javier Alvarado y Angel Sanabria

Convierte una gramática libre de contexto a Forma Normal de Chomsky (CNF) y usa el
algoritmo CYK para decidir si una oración pertenece al lenguaje, mostrando el parse tree
cuando es aceptada.

> **Estado:** pipeline completo: lectura, simplificación, CNF, CYK (con tiempo) y parse
> tree, en CLI, API y frontend.

## Video

https://youtu.be/AnPsPB4vs_A

## Estructura

```
proyecto2-toc/
├── motor/                 # Python, única fuente de verdad
│   ├── gramatica.py       # lector .txt → JSON          (Javier)
│   ├── simplificacion.py  # ε, unitarias, inútiles      (Javier)
│   ├── cnf.py             # conversión a CNF            (Javier)
│   ├── cyk.py             # tokenizador + CYK + tiempo  (Angel)
│   ├── arbol.py           # parse tree                  (Angel)
│   └── main.py            # CLI del pipeline completo   (Angel)
├── backend/
│   ├── app.py             # FastAPI /cyk                (Angel)
│   └── Dockerfile
├── frontend/              # Vite + React (+ Dockerfile)
├── gramaticas/            # 1.txt, 1-cnf.txt, ingles.txt
├── tests/
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Formato de las gramáticas

Un archivo `.txt` en `gramaticas/`, una variable por línea, alternativas separadas por `|`
y símbolos separados por espacios. `e` (o el símbolo unicode `ε`) representa ε.

```
E -> T X
X -> + T X | e
T -> F Y
Y -> * F Y | e
F -> ( E ) | id
```

- `#` inicia un comentario en cualquier parte de la línea (no solo al principio).
- La cabeza de una regla debe ser un solo nombre: empieza con una letra y sigue con letras,
  dígitos, `_` o `'` (p. ej. `E'` es válida).
- Un símbolo que empieza con mayúscula y no tiene ninguna regla se trata como terminal por
  convención (no es error); se reporta en la lista `advertencias` del JSON y se muestra en
  el frontend y el CLI.
- El archivo puede empezar con BOM; se descarta al leerlo.
- `motor/limites.py` define los límites que evitan que una entrada cuelgue la app: líneas,
  símbolos por cuerpo, caracteres de la gramática, anulables por cuerpo, tokens y
  caracteres de la oración. Si alguno se excede, se lanza `ValueError` con un mensaje claro.

La oración se tokeniza contra los terminales de la gramática: primero por espacios y, si un
trozo no es terminal, se parte contra los terminales con retroceso (backtracking), prefiriendo
siempre el más largo (así `(id*id)+id` funciona sin espacios, y `abc` con terminales
`{a, ab, bc}` da `["a", "bc"]` en vez de fallar tras tomar `"ab"`). Si algo no coincide se
intenta en minúsculas (`She` → `she`).

Para ver el JSON que produce el lector:

```
python -m motor.gramatica gramaticas/1.txt
```

## CLI (entrada textual)

Desde la raíz del proyecto:

```
python -m motor.main gramaticas/ingles.txt "She eats a cake with a fork"
python -m motor.main gramaticas/1.txt "(id*id)+id" "id+"
python -m motor.main gramaticas/ingles.txt                    # pide oraciones por consola
python -m motor.main gramaticas/ingles.txt "he cooks" --solo-resultado
python -m motor.main gramaticas/ingles.txt "he cooks" --json  # JSON completo del pipeline
```

Imprime los pasos de simplificación y CNF, la tabla CYK, **SÍ/NO**, el **tiempo** que tardó CYK
y el **parse tree** en notación de corchetes (con y sin las variables auxiliares de la CNF).

## CYK y parse tree

- `motor/cyk.py` llena la tabla por largo de subcadena. Cada celda guarda, además de las
  variables, *backpointers* `(k, B, C)` (o el token, en las hojas). Así el parse tree se arma
  sin volver a correr el algoritmo. Complejidad O(n³·|R|).
- El tiempo se mide con `time.perf_counter()` solo sobre el llenado de la tabla y la decisión.
- `motor/arbol.py` baja desde el símbolo inicial en la celda `[0][n-1]`. Si la oración es
  ambigua se muestra el primer árbol y se informa cuántos hay. La vista "sin auxiliares" quita
  las variables creadas en la CNF (L, R, P, M, Z, W, V…) subiendo sus hijos.
- Si ε pertenece al lenguaje original, la oración vacía se acepta aparte (la CNF no tiene ε).

## Tests

Desde la raíz del proyecto (solo usa la librería estándar; los tests del backend se saltan si
no está instalado `httpx`):

```
python -m unittest discover tests
```

`tests/test_cyk.py` incluye una prueba de equivalencia: la CNF que genera el motor a partir de
`1.txt` y la CNF hecha a mano (`1-cnf.txt`) deciden igual con CYK para **todas** las cadenas de
hasta 6 símbolos sobre `{id, (, ), +, *}`.

## Levantar con Docker

Requiere Docker Desktop abierto. Desde la raíz del proyecto:

```
docker compose up --build
```

| Servicio | URL                        |
| -------- | -------------------------- |
| Frontend | http://localhost:5173      |
| Backend  | http://localhost:8000      |
| API docs | http://localhost:8000/docs |

Ambos servicios se recargan solos al guardar cambios en `motor/`, `backend/`,
`gramaticas/` o `frontend/`, sin reconstruir. Solo hace falta `--build` de nuevo si cambian
`requirements.txt` o `frontend/package.json`.

Para apagarlo: `docker compose down`.

## Levantar sin Docker

Backend (Python 3.12):

```
pip install -r requirements.txt
uvicorn backend.app:app --reload --port 8000
```

Frontend (Node 22), en otra terminal:

```
cd frontend
npm install
npm run dev
```

En desarrollo, Vite redirige `/cyk` al backend en `localhost:8000`.

## API

| Método | Ruta     | Descripción                                    |
| ------ | -------- | ---------------------------------------------- |
| GET    | `/salud` | Comprueba que el backend está arriba           |
| POST   | `/gramatica` | Recibe `{ "gramatica": str }`; devuelve la gramática leída, los pasos de simplificación, la CNF y sus pasos |
| POST   | `/cyk`   | Recibe `{ "gramatica": str, "oracion": str }` (`oracion` es opcional, por defecto `""`); devuelve todo lo de `/gramatica` más `cyk` (tokens, tabla, pasos, `acepta`, `tiempo_ms`, `num_arboles`) y `arbol` |

Ambas rutas devuelven también `advertencias` (lista de avisos que no son error, p. ej. un
símbolo con mayúscula sin reglas).

Códigos de respuesta:

- **400** — gramática inválida, lenguaje vacío, o algún límite de `motor/limites.py` excedido;
  el cuerpo es `{"detail": "mensaje"}`.
- **422** — el cuerpo de la petición no cumple el esquema (p. ej. `oracion` más larga que el
  límite permitido); el cuerpo es el formato estándar de validación de FastAPI/pydantic.
- **500** — un error no previsto del servidor; el cuerpo es `{"detail": "Error interno del motor"}`
  sin traceback (el error completo queda en los logs del backend).

Si `num_arboles` supera el entero más grande que JavaScript representa exacto
(`Number.MAX_SAFE_INTEGER`, 2^53-1), se manda como string en vez de number.

## Ejemplos

| Oración (`ingles.txt`) | Resultado |
| ---------------------- | --------- |
| She eats a cake with a fork | SÍ |
| The cat drinks the beer | SÍ |
| he cuts the meat in the oven | SÍ |
| the dog eats the soup with a spoon in the oven | SÍ |
| the soup eats a knife | SÍ (sintácticamente correcta, aunque no tenga sentido) |
| she cooks | SÍ |
| the cat | NO (falta el verbo) |
| she eats cake | NO (falta el determinante) |
| eats she | NO |
| a cat with a fork | NO |
| she eats a pizza | NO (`pizza` no está en el alfabeto) |

| Oración (`1.txt`) | Resultado |
| ----------------- | --------- |
| `(id*id)+id`, `id + id * id`, `((id))` | SÍ |
| `id+`, `(id`, `id id` | NO |

Con estas oraciones CYK tarda del orden de decenas de microsegundos.
