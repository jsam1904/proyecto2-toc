import Producciones from "../components/Producciones.jsx";

function Chips({ titulo, simbolos, clase }) {
  return (
    <div className="chips">
      <span className="cinta-titulo">{titulo}</span>
      <div className="chips-lista">
        {simbolos.map((s) => (
          <span key={s} className={`chip ${clase}`}>
            {s}
          </span>
        ))}
      </div>
    </div>
  );
}

/** Pestaña Gramática: lo que leyó motor/gramatica.py del .txt. */
export default function Gramatica({ gramatica }) {
  const total = Object.values(gramatica.producciones).reduce((n, c) => n + c.length, 0);
  return (
    <section className="pestana">
      <div className="resumen">
        <p className="resultado-linea">
          Símbolo inicial <span className="simbolo-var">{gramatica.inicial}</span> ·{" "}
          {gramatica.variables.length} variables · {gramatica.terminales.length} terminales · {total}{" "}
          producciones
        </p>
        <Chips titulo="Variables" simbolos={gramatica.variables} clase="simbolo-var" />
        <Chips titulo="Terminales" simbolos={gramatica.terminales} clase="simbolo-term" />
      </div>
      <Producciones gramatica={gramatica} />
      <details className="json">
        <summary>JSON generado</summary>
        <pre>{JSON.stringify(gramatica, null, 2)}</pre>
      </details>
    </section>
  );
}
