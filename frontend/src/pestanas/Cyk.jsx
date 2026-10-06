import { useMemo } from "react";
import Pasos from "../components/Pasos.jsx";

const conjunto = (xs) => (xs.length ? xs.join(" ") : "∅");

/**
 * Pirámide CYK: fila = largo de la subcadena (arriba la frase completa),
 * columna = posición donde empieza. Solo muestra las celdas ya llenadas.
 *
 * @param {object} props
 * @param {object} props.cyk           Resultado de motor.cyk.ejecutar_cyk().
 * @param {Set<string>} props.hasta    Claves "i,j" de las celdas ya llenadas hasta el paso actual.
 * @param {string} props.actual        Clave "i,j" de la celda del paso actual.
 * @param {Set<string>} props.resaltadas  Claves "i,j" de las celdas fuente del paso actual.
 */
function Piramide({ cyk, hasta, actual, resaltadas }) {
  const n = cyk.n;
  const filas = [];
  for (let largo = n; largo >= 1; largo--) {
    const celdas = [];
    for (let i = 0; i + largo - 1 < n; i++) {
      const j = i + largo - 1;
      const clave = `${i},${j}`;
      const llena = hasta.has(clave);
      let clase = "cyk-celda";
      if (clave === actual) clase += " celda-activa";
      else if (resaltadas.has(clave)) clase += " cyk-fuente";
      if (llena && cyk.tabla[i][j].length === 0) clase += " cyk-vacia";
      const esRaiz = largo === n && llena && cyk.acepta;
      celdas.push(
        <div key={i} className={clase + (esRaiz ? " cyk-raiz" : "")} title={`w[${i + 1}..${j + 1}]`}>
          {llena ? conjunto(cyk.tabla[i][j]) : ""}
        </div>
      );
    }
    filas.push(
      <div key={largo} className="cyk-fila" style={{ gridTemplateColumns: `2.2rem repeat(${n}, minmax(3.2rem, 1fr))` }}>
        <span className="cyk-largo">{largo}</span>
        {celdas}
      </div>
    );
  }
  return (
    <div className="cyk-piramide">
      {filas}
      <div className="cyk-fila" style={{ gridTemplateColumns: `2.2rem repeat(${n}, minmax(3.2rem, 1fr))` }}>
        <span className="cyk-largo"></span>
        {cyk.tokens.map((t, k) => (
          <span key={k} className="cyk-token">
            {t}
          </span>
        ))}
      </div>
    </div>
  );
}

/**
 * Pestaña CYK: tabla y pasos de motor/cyk.py, recorribles con <Pasos>.
 * @param {object} props
 * @param {object} props.data  Respuesta completa de /cyk (incluye cyk, gramatica, epsilon_en_lenguaje).
 */
export default function Cyk({ data }) {
  const cyk = data.cyk;
  const orden = useMemo(() => cyk.pasos.map((p) => `${p.i},${p.j}`), [cyk]);

  if (cyk.error_tokens) {
    return (
      <section className="pestana">
        <p className="error">
          No se puede tokenizar la frase: {cyk.error_tokens}. Resultado: <b>NO</b>.
        </p>
      </section>
    );
  }
  if (cyk.n === 0) {
    return (
      <section className="pestana">
        <p className="vacio">
          Frase vacía: se acepta solo si ε ∈ L(G) ({data.epsilon_en_lenguaje ? "sí" : "no"}).
        </p>
      </section>
    );
  }

  return (
    <section className="pestana">
      <Pasos
        pasos={cyk.pasos}
        velocidadMs={700}
        render={(paso, idx) => {
          const hasta = new Set(orden.slice(0, idx + 1));
          const resaltadas = new Set();
          if (paso.tipo === "combinacion") {
            for (const p of paso.particiones) {
              if (p.reglas.length) {
                resaltadas.add(p.izquierda.join(","));
                resaltadas.add(p.derecha.join(","));
              }
            }
          }
          const sub = cyk.tokens.slice(paso.i, paso.j + 1).join(" ");
          return (
            <div className="dos-columnas-lateral">
              <div className="explicacion">
                <p>
                  Celda <b>[{paso.i + 1}, {paso.j + 1}]</b> — subcadena <code>{sub}</code>
                </p>
                {paso.tipo === "terminal" ? (
                  <p>
                    Variables con <code>A → {paso.token}</code>:{" "}
                    {paso.reglas.length ? <code>{paso.reglas.join(", ")}</code> : "ninguna"}
                  </p>
                ) : (
                  <ul className="particiones">
                    {paso.particiones.map((p) => (
                      <li key={p.k} className={p.reglas.length ? "" : "sin-reglas"}>
                        corte k={p.k + 1}: <code>{conjunto(p.vars_izquierda)}</code> ×{" "}
                        <code>{conjunto(p.vars_derecha)}</code>
                        {p.reglas.length ? (
                          <>
                            {" "}
                            ⇒ <code>{p.reglas.join(", ")}</code>
                          </>
                        ) : (
                          " ⇒ nada"
                        )}
                      </li>
                    ))}
                  </ul>
                )}
                <p>
                  Resultado: <code className="postfix">{conjunto(paso.resultado)}</code>
                </p>
                {idx === cyk.pasos.length - 1 && (
                  <p>
                    {data.gramatica.inicial} {cyk.acepta ? "está" : "no está"} en la celda de toda la frase ⇒{" "}
                    <span className={"veredicto " + (cyk.acepta ? "si" : "no")}>{cyk.acepta ? "SÍ" : "NO"}</span>
                  </p>
                )}
              </div>
              <Piramide cyk={cyk} hasta={hasta} actual={`${paso.i},${paso.j}`} resaltadas={resaltadas} />
            </div>
          );
        }}
      />
      <p className="nota">ámbar = celda que se llena · azul = celdas que se combinaron · fila = largo de la subcadena</p>
    </section>
  );
}
