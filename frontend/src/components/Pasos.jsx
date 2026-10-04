import { useEffect, useState } from "react";

/**
 * Recorre una lista de pasos con slider, botones y reproducción automática.
 * No sabe qué es un paso: `render(paso, indice)` decide cómo se muestra.
 *
 * Teclado (con el foco en el control): ← → mueven un paso, espacio reproduce.
 */
export default function Pasos({ pasos, render, velocidadMs = 900 }) {
  const [i, setI] = useState(0);
  const [reproduciendo, setReproduciendo] = useState(false);
  const total = pasos.length;
  const ultimo = total - 1;

  useEffect(() => {
    setI(0);
    setReproduciendo(false);
  }, [pasos]);

  useEffect(() => {
    if (!reproduciendo) return undefined;
    if (i >= ultimo) {
      setReproduciendo(false);
      return undefined;
    }
    const t = setTimeout(() => setI((v) => Math.min(v + 1, ultimo)), velocidadMs);
    return () => clearTimeout(t);
  }, [reproduciendo, i, ultimo, velocidadMs]);

  const ir = (n) => setI(Math.max(0, Math.min(n, ultimo)));

  const onKeyDown = (ev) => {
    if (ev.key === "ArrowRight") ir(i + 1);
    else if (ev.key === "ArrowLeft") ir(i - 1);
    else if (ev.key === " ") {
      ev.preventDefault();
      setReproduciendo((v) => !v);
    } else return;
    ev.stopPropagation();
  };

  if (total === 0) return <p className="vacio">No hay pasos para mostrar.</p>;

  // Si llega una lista más corta, `i` aún apunta a la anterior hasta que corre el efecto.
  const actual = Math.min(i, ultimo);

  return (
    <div className="pasos" tabIndex={0} onKeyDown={onKeyDown}>
      <div className="pasos-controles">
        <button type="button" onClick={() => ir(0)} disabled={i === 0} aria-label="Primer paso">
          ⏮
        </button>
        <button type="button" onClick={() => ir(i - 1)} disabled={i === 0} aria-label="Paso anterior">
          ◀
        </button>
        <button
          type="button"
          className="pasos-play"
          onClick={() => {
            if (i >= ultimo) ir(0);
            setReproduciendo((v) => !v);
          }}
        >
          {reproduciendo ? "Pausar" : "Reproducir"}
        </button>
        <button type="button" onClick={() => ir(i + 1)} disabled={i === ultimo} aria-label="Paso siguiente">
          ▶
        </button>
        <button type="button" onClick={() => ir(ultimo)} disabled={i === ultimo} aria-label="Último paso">
          ⏭
        </button>
        <input
          type="range"
          min={0}
          max={ultimo}
          value={i}
          onChange={(ev) => ir(Number(ev.target.value))}
          aria-label="Paso"
        />
        <span className="pasos-contador">
          {actual + 1} / {total}
        </span>
      </div>
      <div className="pasos-contenido">{render(pasos[actual], actual)}</div>
    </div>
  );
}
