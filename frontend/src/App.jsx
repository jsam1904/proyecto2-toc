import { useEffect, useState } from "react";
import { ejecutarCyk } from "./api.js";
import Arbol from "./pestanas/Arbol.jsx";
import Cnf from "./pestanas/Cnf.jsx";
import Cyk from "./pestanas/Cyk.jsx";
import Gramatica from "./pestanas/Gramatica.jsx";
import Simplificacion from "./pestanas/Simplificacion.jsx";

// Copias de gramaticas/1.txt e ingles.txt.
const EJEMPLOS = {
  expresiones: {
    nombre: "Expresiones (1.txt)",
    oracion: "id + id * id",
    gramatica: `E -> T X
X -> + T X | e
T -> F Y
Y -> * F Y | e
F -> ( E ) | id`,
  },
  ingles: {
    nombre: "Inglés (ingles.txt)",
    oracion: "she eats a cake with a fork",
    gramatica: `S -> NP VP
VP -> VP PP
VP -> V NP
VP -> cooks | drinks | eats | cuts
PP -> P NP
NP -> Det N
NP -> he | she
V -> cooks | drinks | eats | cuts
P -> in | with
N -> cat | dog
N -> beer | cake | juice | meat | soup
N -> fork | knife | oven | spoon
Det -> a | the`,
  },
};

const PESTANAS = [
  {
    id: "gramatica",
    nombre: "Gramática",
    modulo: "motor/gramatica.py",
    responsable: "Javier",
    mostrara: ["Producciones leídas del .txt", "Variables, terminales y símbolo inicial"],
  },
  {
    id: "simplificacion",
    nombre: "Simplificación",
    modulo: "motor/simplificacion.py",
    responsable: "Javier",
    mostrara: ["Eliminación de producciones ε", "Eliminación de unitarias", "Eliminación de símbolos inútiles"],
  },
  {
    id: "cnf",
    nombre: "CNF",
    modulo: "motor/cnf.py",
    responsable: "Javier",
    mostrara: ["Gramática en Forma Normal de Chomsky"],
  },
  {
    id: "cyk",
    nombre: "CYK",
    modulo: "motor/cyk.py",
    responsable: "Angel",
    mostrara: ["Tokens de la oración", "Tabla CYK", "Veredicto (sí / no) y tiempo de ejecución"],
  },
  {
    id: "arbol",
    nombre: "Árbol",
    modulo: "motor/arbol.py",
    responsable: "Angel",
    mostrara: ["Parse tree de la oración si es aceptada"],
  },
];

/**
 * Página completa: formulario de gramática/oración, pestañas y veredicto.
 * @param {object} props  Sin props; el estado vive aquí (gramática, oración, resultado).
 */
export default function App() {
  const [gramatica, setGramatica] = useState(EJEMPLOS.expresiones.gramatica);
  const [oracion, setOracion] = useState(EJEMPLOS.expresiones.oracion);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);
  const [pestana, setPestana] = useState("gramatica");
  const [datos, setDatos] = useState(null); // respuesta de /cyk (incluye todo lo de /gramatica)

  async function ejecutar(texto = gramatica, w = oracion) {
    setCargando(true);
    setError("");
    try {
      setDatos(await ejecutarCyk(texto, w));
    } catch (e) {
      setError(e.message);
      setDatos(null);
    } finally {
      setCargando(false);
    }
  }

  function cargarEjemplo(id) {
    const ejemplo = EJEMPLOS[id];
    setGramatica(ejemplo.gramatica);
    setOracion(ejemplo.oracion);
    ejecutar(ejemplo.gramatica, ejemplo.oracion);
  }

  useEffect(() => {
    ejecutar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function contenido() {
    if (!datos) {
      return (
        <p className="inicio-vacio">
          {cargando ? "Calculando…" : "Escribe una gramática y una oración y presiona Ejecutar."}
        </p>
      );
    }
    if (pestana === "gramatica") return <Gramatica gramatica={datos.gramatica} />;
    if (pestana === "simplificacion") return <Simplificacion pasos={datos.simplificacion} />;
    if (pestana === "cnf") return <Cnf cnf={datos.cnf} pasos={datos.pasos_cnf} />;
    if (pestana === "cyk") return <Cyk data={datos} />;
    return <Arbol data={datos} />;
  }

  const ms = (x) => (x < 1 ? `${(x * 1000).toFixed(1)} µs` : `${x.toFixed(3)} ms`);

  return (
    <div className="app">
      <header className="cabecera">
        <div className="titulo">
          <h1>Gramáticas libres de contexto: CNF y algoritmo CYK</h1>
          <p>Teoría de la Computación · Proyecto No. 2 · Javier Alvarado y Angel Sanabria</p>
        </div>

        <div className="formulario">
          <label>
            <span>Gramática</span>
            <textarea
              value={gramatica}
              onChange={(e) => setGramatica(e.target.value)}
              spellCheck={false}
              autoComplete="off"
            />
          </label>
          <label>
            <span>Oración w</span>
            <input
              value={oracion}
              onChange={(e) => setOracion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && ejecutar()}
              spellCheck={false}
              autoComplete="off"
            />
          </label>
          <button
            type="button"
            className="primario"
            onClick={() => ejecutar()}
            disabled={cargando || !gramatica.trim()}
          >
            {cargando ? "Calculando…" : "Ejecutar"}
          </button>
          <select
            className="ejemplos"
            value=""
            onChange={(e) => e.target.value && cargarEjemplo(e.target.value)}
            aria-label="Cargar ejemplo"
          >
            <option value="">Cargar ejemplo…</option>
            {Object.entries(EJEMPLOS).map(([id, ej]) => (
              <option key={id} value={id}>
                {ej.nombre}
              </option>
            ))}
          </select>
        </div>
        {error && <p className="error">{error}</p>}
        {datos?.advertencias?.length > 0 && (
          <ul className="advertencias">
            {datos.advertencias.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
        )}

        {datos && (
          <div className="veredicto-barra">
            <span className={"veredicto grande " + (datos.cyk.acepta ? "si" : "no")}>
              {datos.cyk.acepta ? "SÍ" : "NO"}
            </span>
            <span>
              w {datos.cyk.acepta ? "∈" : "∉"} L(G)
              {datos.cyk.error_tokens && ` — ${datos.cyk.error_tokens}`}
            </span>
            <span className="tiempo">CYK: {ms(datos.cyk.tiempo_ms)}</span>
            <span className="tiempo">simplificación + CNF: {ms(datos.tiempo_conversion_ms)}</span>
            {datos.cyk.num_arboles > 1 && <span className="tiempo">{datos.cyk.num_arboles} árboles (ambigua)</span>}
          </div>
        )}
      </header>

      <nav className="pestanas-nav" aria-label="Etapas">
        {PESTANAS.map((p) => (
          <button
            key={p.id}
            type="button"
            className={pestana === p.id ? "activa" : ""}
            onClick={() => setPestana(p.id)}
          >
            {p.nombre}
          </button>
        ))}
      </nav>

      <main>{contenido()}</main>
    </div>
  );
}
