/**
 * Llama al backend. En desarrollo Vite redirige /cyk a localhost:8000.
 * Si la gramática es inválida el backend responde 400 con {detail: "mensaje"}.
 */
export async function ejecutarCyk(gramatica, oracion) {
  let res;
  try {
    res = await fetch("/cyk", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ gramatica, oracion }),
    });
  } catch {
    throw new Error("No se pudo conectar con el backend. ¿Está corriendo en el puerto 8000?");
  }
  if (!res.ok) {
    let mensaje = `El backend respondió ${res.status}`;
    try {
      const cuerpo = await res.json();
      if (cuerpo.detail) mensaje = cuerpo.detail;
    } catch {
      /* sin cuerpo JSON */
    }
    throw new Error(mensaje);
  }
  return res.json();
}
