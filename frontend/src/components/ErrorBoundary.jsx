import { Component } from "react";

/**
 * Atrapa errores de render en sus hijos y muestra un mensaje en vez de pantalla en blanco.
 * @param {object} props
 * @param {import("react").ReactNode} props.children
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error("Error de render:", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="error" style={{ margin: "2rem" }}>
          <h1>Algo salió mal</h1>
          <p>{this.state.error.message || String(this.state.error)}</p>
        </div>
      );
    }
    return this.props.children;
  }
}
