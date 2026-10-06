import Pasos from "../components/Pasos.jsx";
import { PasoGramatica } from "../components/Producciones.jsx";

/**
 * Pestaña Simplificación: pasos de motor/simplificacion.py (ε, unitarias, inútiles).
 * @param {object} props
 * @param {Array} props.pasos  Pasos devueltos por motor.simplificacion.simplificar().
 */
export default function Simplificacion({ pasos }) {
  return (
    <section className="pestana">
      <Pasos
        pasos={pasos}
        render={(paso, i) => <PasoGramatica paso={paso} anterior={i > 0 ? pasos[i - 1].gramatica : null} />}
      />
    </section>
  );
}
