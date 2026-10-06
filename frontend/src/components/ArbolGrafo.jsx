import { useEffect, useRef } from "react";
import cytoscape from "cytoscape";
import dagre from "cytoscape-dagre";

cytoscape.use(dagre);

// Mismo lenguaje visual que los autómatas del Proyecto 1 (pizarra):
// variables en óvalo, terminales (hojas) en azul y sin borde,
// variables auxiliares de la CNF punteadas.
const ESTILO = [
  {
    selector: "node",
    style: {
      shape: "round-rectangle",
      width: "label",
      height: 38,
      padding: 10,
      "background-color": "#fdfcf8",
      "border-width": 2,
      "border-color": "#1e1e1e",
      label: "data(label)",
      "text-valign": "center",
      "text-halign": "center",
      "font-family": "Architects Daughter, cursive",
      "font-size": 19,
      color: "#1e1e1e",
    },
  },
  {
    selector: "node.hoja",
    style: {
      "border-width": 0,
      "background-color": "#a5d8ff",
      "font-family": "IBM Plex Mono, monospace",
      "font-size": 17,
    },
  },
  { selector: "node.auxiliar", style: { "border-style": "dashed", color: "#6b6b66" } },
  { selector: "node.raiz", style: { "background-color": "#ffec99", "border-color": "#f08c00", "border-width": 3 } },
  {
    selector: "edge",
    style: { width: 1.6, "line-color": "#1e1e1e", "curve-style": "straight", "line-cap": "round" },
  },
];

/**
 * Dibuja un parse tree {nodos:[{id,label,tipo}], aristas:[{id,de,a}]}.
 * @param {object} props
 * @param {object} props.grafo     {nodos, aristas} devuelto por motor/arbol.py: a_grafo().
 * @param {number} [props.altura]  Alto en px del lienzo.
 */
export default function Arbol({ grafo, altura = 420 }) {
  const contenedor = useRef(null);

  useEffect(() => {
    if (!contenedor.current || !grafo) return undefined;
    const elementos = [
      ...grafo.nodos.map((n, k) => ({
        data: { id: n.id, label: n.label },
        classes: n.tipo + (k === 0 ? " raiz" : ""),
      })),
      ...grafo.aristas.map((e) => ({ data: { id: e.id, source: e.de, target: e.a } })),
    ];
    const cy = cytoscape({
      container: contenedor.current,
      elements: elementos,
      style: ESTILO,
      layout: { name: "dagre", rankDir: "TB", nodeSep: 22, rankSep: 46, padding: 16 },
      wheelSensitivity: 0.2,
      boxSelectionEnabled: false,
      autoungrabify: true,
    });
    cy.fit(undefined, 16);
    if (cy.zoom() > 1.4) {
      cy.zoom(1.4);
      cy.center();
    }
    return () => cy.destroy();
  }, [grafo]);

  return <div ref={contenedor} className="automata-lienzo" style={{ height: altura }} />;
}
