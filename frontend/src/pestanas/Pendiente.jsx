/** Marcador para una pestaña cuyo módulo del motor aún no está listo. */
export default function Pendiente({ titulo, modulo, responsable, mostrara }) {
  return (
    <section className="pestana">
      <div className="pendiente">
        <h2>{titulo} — pendiente</h2>
        <p className="nota">
          Depende de <code>{modulo}</code> ({responsable}).
        </p>
        {mostrara && mostrara.length > 0 && (
          <ul>
            {mostrara.map((m) => (
              <li key={m}>{m}</li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
