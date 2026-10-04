import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";

// En desarrollo, /cyk y /gramatica se redirigen al backend de FastAPI (puerto 8000),
// así el frontend no necesita configurar CORS ni URLs absolutas.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/cyk": BACKEND,
      "/gramatica": BACKEND,
    },
  },
});
