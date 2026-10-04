/**
 * Llama al backend. En desarrollo Vite redirige /cyk y /gramatica a localhost:8000.
 * Si la gramática es inválida el backend responde 400 con {detail: "mensaje"}.
 */
async function post(ruta, cuerpo) {
  let res;
  try {
    res = await fetch(ruta, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cuerpo),
    });
  } catch {
    throw new Error("No se pudo conectar con el backend. ¿Está corriendo en el puerto 8000?");
  }
  if (!res.ok) {
    let mensaje = `El backend respondió ${res.status}`;
    try {
      const datos = await res.json();
      if (datos.detail) mensaje = datos.detail;
    } catch {
      /* sin cuerpo JSON */
    }
    throw new Error(mensaje);
  }
  return res.json();
}

/** Fase 1: gramática leída, pasos de simplificación y pasos de CNF. */
export function procesarGramatica(gramatica) {
  return post("/gramatica", { gramatica });
}

export function ejecutarCyk(gramatica, oracion) {
  return post("/cyk", { gramatica, oracion });
}
