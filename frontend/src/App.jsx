import { useState } from "react";
import { ejecutarCyk } from "./api.js";
import Pendiente from "./pestanas/Pendiente.jsx";

const GRAMATICA_EJEMPLO = `E -> T X
X -> + T X | e
T -> F Y
Y -> * F Y | e
F -> ( E ) | id`;

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

export default function App() {
  const [gramatica, setGramatica] = useState(GRAMATICA_EJEMPLO);
  const [oracion, setOracion] = useState("id + id * id");
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);
  const [pestana, setPestana] = useState("gramatica");

  async function ejecutar() {
    setCargando(true);
    setError("");
    try {
      // Las pestañas aún no consumen la respuesta; se conectarán cuando el motor esté listo.
      await ejecutarCyk(gramatica, oracion);
    } catch (e) {
      setError(e.message);
    } finally {
      setCargando(false);
    }
  }

  const actual = PESTANAS.find((p) => p.id === pestana);

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
          <button type="button" className="primario" onClick={ejecutar} disabled={cargando}>
            {cargando ? "Calculando…" : "Ejecutar"}
          </button>
          <button type="button" onClick={() => setGramatica(GRAMATICA_EJEMPLO)}>
            Cargar ejemplo
          </button>
        </div>
        {error && <p className="error">{error}</p>}
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

      <main>
        <Pendiente
          titulo={actual.nombre}
          modulo={actual.modulo}
          responsable={actual.responsable}
          mostrara={actual.mostrara}
        />
      </main>
    </div>
  );
}
