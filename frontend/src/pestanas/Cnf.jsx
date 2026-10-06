import Pasos from "../components/Pasos.jsx";
import { PasoGramatica } from "../components/Producciones.jsx";

/**
 * Pestaña CNF: pasos de motor/cnf.py y la gramática final en formato .txt.
 * @param {object} props
 * @param {object} props.cnf    Gramática final en CNF.
 * @param {Array} props.pasos   Pasos devueltos por motor.cnf.a_cnf().
 */
export default function Cnf({ cnf, pasos }) {
  const total = Object.values(cnf.producciones).reduce((n, c) => n + c.length, 0);
  const texto = pasos[pasos.length - 1].texto;
  return (
    <section className="pestana">
      <p className="resultado-linea">
        Gramática en Forma Normal de Chomsky: {cnf.variables.length} variables · {total} producciones
      </p>
      <Pasos
        pasos={pasos}
        render={(paso, i) => <PasoGramatica paso={paso} anterior={i > 0 ? pasos[i - 1].gramatica : null} />}
      />
      <details className="json">
        <summary>CNF en formato .txt</summary>
        <pre>{texto}</pre>
      </details>
    </section>
  );
}
