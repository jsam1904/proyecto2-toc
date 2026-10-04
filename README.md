# proyecto2-toc

Teoría de la Computación · Proyecto No. 2 · Javier Alvarado y Angel Sanabria

Convierte una gramática libre de contexto a Forma Normal de Chomsky (CNF) y usa el
algoritmo CYK para decidir si una oración pertenece al lenguaje, mostrando el parse tree
cuando es aceptada.

> **Estado:** estructura y Docker listos. El motor (`motor/`) y el endpoint `/cyk` están
> pendientes; mientras tanto `/cyk` responde 501 y las pestañas del frontend aparecen
> como pendientes.

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
y símbolos separados por espacios. `e` representa ε.

```
E -> T X
X -> + T X | e
T -> F Y
Y -> * F Y | e
F -> ( E ) | id
```

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
| POST   | `/cyk`   | Recibe `{ "gramatica": str, "oracion": str }`  |

`/cyk` responde 501 hasta que el motor esté implementado.
