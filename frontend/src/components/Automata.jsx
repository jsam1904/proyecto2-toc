import { useEffect, useRef } from "react";
import cytoscape from "cytoscape";
import dagre from "cytoscape-dagre";

cytoscape.use(dagre);

// Paleta y trazo tomados del lenguaje visual de la pizarra / Excalidraw:
// tinta oscura, rellenos pastel, y el ámbar reservado para lo que está activo.
const ESTILO = [
  {
    selector: "node",
    style: {
      shape: "ellipse",
      width: 40,
      height: 40,
      "background-color": "#fdfcf8",
      "border-width": 2,
      "border-color": "#1e1e1e",
      label: "data(label)",
      "text-valign": "center",
      "text-halign": "center",
      "font-family": "Architects Daughter, cursive",
      "font-size": 15,
      color: "#1e1e1e",
      "transition-property": "background-color, border-color",
      "transition-duration": "0.15s",
    },
  },
  {
    selector: "node.aceptacion",
    style: { "border-style": "double", "border-width": 6 },
  },
  {
    selector: "node.inicio",
    style: {
      width: 1,
      height: 1,
      "background-opacity": 0,
      "border-width": 0,
      label: "",
    },
  },
  {
    selector: "node.activo",
    style: {
      "background-color": "#ffec99",
      "border-color": "#f08c00",
      "border-width": 3,
      color: "#1e1e1e",
    },
  },
  {
    selector: "edge",
    style: {
      "curve-style": "bezier",
      "control-point-step-size": 75,
      "loop-direction": "-90deg",
      "loop-sweep": "40deg",
      width: 1.8,
      "line-cap": "round",
      "line-color": "#1e1e1e",
      "target-arrow-color": "#1e1e1e",
      "target-arrow-shape": "triangle",
      "arrow-scale": 1,
      label: "data(label)",
      "font-family": "Architects Daughter, cursive",
      "font-size": 14,
      color: "#1971c2",
      "text-background-color": "#fdfcf8",
      "text-background-opacity": 1,
      "text-background-padding": 2,
      "text-background-shape": "roundrectangle",
    },
  },
  {
    selector: "edge.activa",
    style: { "line-color": "#f08c00", "target-arrow-color": "#f08c00", width: 3 },
  },
  {
    selector: "edge.bucle",
    style: {
      "loop-direction": "90deg",
      "loop-sweep": "60deg",
      "control-point-step-size": 30,
    },
  },
];

const idNodo = (estado) => `n_${String(estado)}`;

/** Convierte un autómata del contrato a elementos de Cytoscape.
 *  Las transiciones con mismo origen y destino se unen en una sola arista
 *  con etiqueta "a, b" (como se dibuja a mano). */
function aElementos(data) {
  const elementos = [];
  const aceptacion = new Set(data.aceptacion.map(String));

  elementos.push({ data: { id: "inicio" }, classes: "inicio", selectable: false });
  for (const e of data.estados) {
    const clases = aceptacion.has(String(e)) ? "aceptacion" : "";
    elementos.push({ data: { id: idNodo(e), label: String(e) }, classes: clases });
  }

  const agrupadas = new Map();
  for (const t of data.transiciones) {
    const clave = `${t.de}->${t.a}`;
    if (!agrupadas.has(clave)) agrupadas.set(clave, { de: t.de, a: t.a, simbolos: [] });
    agrupadas.get(clave).simbolos.push(t.simbolo);
  }
  elementos.push({
    data: { id: "e_inicio", source: "inicio", target: idNodo(data.inicial), label: "" },
  });
  for (const { de, a, simbolos } of agrupadas.values()) {
    elementos.push({
      data: {
        id: `e_${de}_${a}`,
        source: idNodo(de),
        target: idNodo(a),
        label: simbolos.join(", "),
        de: String(de),
        a: String(a),
      },
      classes: String(de) === String(a) ? "bucle" : "",
    });
  }
  return elementos;
}

/**
 * Dibuja un AFN/AFD del contrato.
 *
 * @param {object} data       Autómata con la forma del contrato (sección 3).
 * @param {Array}  resaltar   Estados a pintar como activos.
 * @param {Array}  aristas    [{de, a}] transiciones a resaltar (opcional).
 * @param {string} titulo     Pie de figura.
 * @param {number} altura     Alto en px del lienzo.
 */
export default function Automata({ data, resaltar = [], aristas = [], titulo, altura = 300 }) {
  const contenedor = useRef(null);
  const cy = useRef(null);

  useEffect(() => {
    if (!contenedor.current || !data) return;
    cy.current = cytoscape({
      container: contenedor.current,
      elements: aElementos(data),
      style: ESTILO,
      layout: { name: "dagre", rankDir: "LR", nodeSep: 65, rankSep: 130, padding: 16 },
      userZoomingEnabled: true,
      wheelSensitivity: 0.2,
      boxSelectionEnabled: false,
      autoungrabify: true,
    });
    cy.current.fit(undefined, 16);
    if (cy.current.zoom() > 1.15) {
      cy.current.zoom(1.15);
      cy.current.center();
    }
    return () => {
      cy.current?.destroy();
      cy.current = null;
    };
  }, [data]);

  useEffect(() => {
    const instancia = cy.current;
    if (!instancia) return;
    const activos = new Set(resaltar.map(String));
    instancia.nodes().forEach((n) => {
      n.toggleClass("activo", activos.has(n.data("label")));
    });
    const activas = new Set(aristas.map((a) => `${a.de}->${a.a}`));
    instancia.edges().forEach((e) => {
      e.toggleClass("activa", activas.has(`${e.data("de")}->${e.data("a")}`));
    });
  }, [resaltar, aristas, data]);

  return (
    <figure className="automata">
      {titulo && <figcaption>{titulo}</figcaption>}
      <div ref={contenedor} className="automata-lienzo" style={{ height: altura }} />
    </figure>
  );
}
