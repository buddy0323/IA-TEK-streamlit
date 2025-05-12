import streamlit as st
import requests
from auth.auth import requires_permission
from utils.helpers import render_sidebar
from database.database import get_db_session
from database.models import Agent
from utils.styles import apply_global_styles

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
    # st.title("🧠 I waited for two weeks. Johnatan George, Pay me quickly. You are a scammer.")
    st.caption("Gestiona el conocimiento y mejora el rendimiento de tus agentes.")

    st.markdown("---")
    st.header("Cargar Documentos para Entrenamiento")
    uploaded_files = st.file_uploader(
        "Sube uno o más archivos (PDF, TXT, CSV, etc.) para entrenar un agente específico.",
        type=["pdf", "txt", "csv"],
        accept_multiple_files=True
    )

    st.header("Selecciona el método de procesamiento")
    processing_method = st.radio(
        "¿Cómo deseas procesar los documentos?",
        ("Chunking", "Embedding"),
        horizontal=True
    )

    st.header("Selecciona el agente a entrenar")
    with get_db_session() as db:
        active_agents = db.query(Agent).filter(Agent.status == 'active').all()
        agent_options = {f"{agent.name}": agent for agent in active_agents}
        if not agent_options:
            st.warning("No hay agentes activos disponibles para entrenamiento.")
            return
        selected_label = st.selectbox("Agente activo:", list(agent_options.keys()))
        selected_agent = agent_options[selected_label]

        if uploaded_files and st.button("Entrenar"):
            # Prepare files for sending
            files = []
            for file in uploaded_files:
                files.append(("files", (file.name, file, file.type)))
            # Prepare data
            data = {
                "agent_id": selected_agent.id,
                "processing_method": processing_method.lower(),
            }
            # Get n8n workflow URL
            n8n_url = selected_agent.n8n_details_url
            if not n8n_url:
                st.toast("❌ El agente seleccionado no tiene una URL n8n configurada.", icon="❌")
                return
            try:
                response = requests.post(n8n_url, data=data, files=files)
                if response.status_code == 200:
                    st.toast("✅ El agente fue entrenado con éxito.", icon="✅")
                else:
                    st.toast("❌ El entrenamiento del agente falló.", icon="❌")
            except Exception as e:
                st.toast(f"❌ Error al conectar con el workflow de n8n: {e}", icon="❌")

# --- Ejecutar la Página ---
# No se necesita el bloque if __name__ == "__main__"
# app.py y el decorador gestionan la ejecución y protección.
apply_global_styles()
show_entrenar_page()
