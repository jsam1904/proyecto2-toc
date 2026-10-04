const clave = (cuerpo) => JSON.stringify(cuerpo);

/** Un cuerpo de producción: variables en tinta, terminales en azul, ε aparte. */
function Cuerpo({ cuerpo, esVariable }) {
  if (cuerpo.length === 0) return <span className="simbolo-eps">ε</span>;
  return cuerpo.map((s, i) => (
    <span key={i} className={esVariable(s) ? "simbolo-var" : "simbolo-term"}>
      {s}
    </span>
  ));
}

/**
 * Tabla de producciones de una gramática del motor ({inicial, variables, producciones}).
 * Si se pasa `anterior`, marca en ámbar lo nuevo y tacha lo eliminado respecto a ella.
 */
export default function Producciones({ gramatica, anterior = null }) {
  const prods = gramatica.producciones;
  const previas = anterior?.producciones ?? {};
  const esVariable = (s) => s in prods || s in previas;

  const filas = gramatica.variables.map((v) => ({ v, quitada: false }));
  if (anterior) {
    for (const v of anterior.variables) {
      if (!(v in prods)) filas.push({ v, quitada: true });
    }
  }

  return (
    <div className="producciones">
      <table className="tabla-producciones">
        <tbody>
          {filas.map(({ v, quitada }) => {
            const actuales = prods[v] ?? [];
            const antes = previas[v] ?? [];
            const clavesActuales = new Set(actuales.map(clave));
            const clavesAntes = new Set(antes.map(clave));
            const alternativas = [
              ...actuales.map((c) => ({
                c,
                estado: anterior && !clavesAntes.has(clave(c)) ? "nueva" : "",
              })),
              ...(anterior
                ? antes.filter((c) => !clavesActuales.has(clave(c))).map((c) => ({ c, estado: "quitada" }))
                : []),
            ];
            return (
              <tr key={v} className={quitada ? "fila-quitada" : ""}>
                <th scope="row">
                  <span className="simbolo-var">{v}</span>
                  {v === gramatica.inicial && <span className="marca-inicial" title="Símbolo inicial">inicial</span>}
                </th>
                <td className="flecha">→</td>
                <td>
                  {alternativas.length === 0 && <span className="simbolo-eps">∅</span>}
                  {alternativas.map(({ c, estado }, i) => (
                    <span key={clave(c) + estado} className="alternativa-grupo">
                      {i > 0 && <span className="barra">|</span>}
                      <span className={`alternativa ${estado}`}>
                        <Cuerpo cuerpo={c} esVariable={esVariable} />
                      </span>
                    </span>
                  ))}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {anterior && (
        <p className="leyenda">
          <span className="alternativa nueva">nueva</span>
          <span className="alternativa quitada">eliminada</span>
          respecto al paso anterior
        </p>
      )}
    </div>
  );
}

/** Un paso del motor ({titulo, detalle, gramatica}) con su tabla, comparado con el paso previo. */
export function PasoGramatica({ paso, anterior }) {
  return (
    <div className="paso-gramatica">
      <h3>{paso.titulo}</h3>
      <p className="accion">{paso.detalle}</p>
      <Producciones gramatica={paso.gramatica} anterior={anterior} />
    </div>
  );
}
