import { useState } from "react";
import ArbolGrafo from "../components/ArbolGrafo.jsx";

/**
 * Pestaña Árbol: parse tree de motor/arbol.py, con vista CNF o sin auxiliares.
 * @param {object} props
 * @param {object} props.data  Respuesta completa de /cyk (incluye arbol y cyk).
 */
export default function Arbol({ data }) {
  const [vista, setVista] = useState("simplificado");
  const arbol = data.arbol;

  if (!arbol) {
    return (
      <section className="pestana">
        <p className="vacio">
          {data.cyk.acepta
            ? "La frase vacía se acepta porque ε ∈ L(G); no hay árbol que dibujar."
            : "La frase no pertenece al lenguaje, así que no hay parse tree."}
        </p>
      </section>
    );
  }

  const grafo = vista === "cnf" ? arbol.cnf : arbol.simplificado;
  return (
    <section className="pestana">
      <div className="selector">
        <button type="button" className={vista === "simplificado" ? "activo" : ""} onClick={() => setVista("simplificado")}>
          Sin variables auxiliares
        </button>
        <button type="button" className={vista === "cnf" ? "activo" : ""} onClick={() => setVista("cnf")}>
          Árbol de la CNF
        </button>
      </div>
      {data.cyk.num_arboles > 1 && (
        <p className="aviso">
          La frase es ambigua: hay {data.cyk.num_arboles} parse trees distintos. Se muestra el primero que encontró
          CYK.
        </p>
      )}
      <ArbolGrafo grafo={grafo} altura={Math.min(760, 120 + 90 * profundidad(grafo))} />
      <p className="resultado-linea">
        <code>{vista === "cnf" ? arbol.corchetes_cnf : arbol.corchetes_simplificado}</code>
      </p>
      <p className="nota">
        {vista === "cnf"
          ? "Las variables punteadas las creó la conversión a CNF."
          : "Se quitaron las variables auxiliares de la CNF subiendo sus hijos: se lee con la gramática simplificada."}
      </p>
    </section>
  );
}

function profundidad(grafo) {
  const hijos = new Map();
  for (const e of grafo.aristas) {
    if (!hijos.has(e.de)) hijos.set(e.de, []);
    hijos.get(e.de).push(e.a);
  }
  const prof = (id) => 1 + Math.max(0, ...(hijos.get(id) || []).map(prof));
  return grafo.nodos.length ? prof(grafo.nodos[0].id) : 0;
}
