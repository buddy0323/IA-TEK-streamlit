import streamlit as st

# Importar dependencias locales
from auth.auth import requires_permission # Decorador para proteger página
from utils.helpers import show_dev_placeholder # Helper para mostrar mensaje "en desarrollo"
from utils.helpers import render_sidebar # <-- AÑADIR ESTA LÍNEA

# --- LLAMAR A RENDER_SIDEBAR TEMPRANO ---
render_sidebar()
# --- FIN LLAMADA ---

# Permiso requerido para acceder a esta página (ajustar si es necesario)
PAGE_PERMISSION = "Entrenar" # O podría ser un permiso más específico

@requires_permission(PAGE_PERMISSION)
def show_entrenar_page():
    """
    Muestra la página de Entrenamiento de Agentes (actualmente en desarrollo).
    """
    st.title("🧠 Entrenamiento de Agentes IA")
    st.caption("Gestiona el conocimiento y mejora el rendimiento de tus agentes.")

    # Mostrar el mensaje estándar de "en desarrollo"
    show_dev_placeholder("Entrenamiento de Agentes")

    # --- Notas para Futura Implementación ---
    st.markdown("---")
    st.markdown("""
    **Funcionalidades Futuras Posibles:**
    * Carga de documentos (PDF, TXT, CSV) para entrenar agentes específicos.
    * Conexión con bases de datos de conocimiento externas.
    * Interfaz para iniciar/monitorear flujos de entrenamiento en N8N o CrewAI.
    * Visualización del estado del último entrenamiento por agente.
    * Gestión de conjuntos de datos de entrenamiento.
    """)

# --- Ejecutar la Página ---
# No se necesita el bloque if __name__ == "__main__"
# app.py y el decorador gestionan la ejecución y protección.
show_entrenar_page()
