# --- pages/03_Agentes_IA.py (CORREGIDO - Evitar DetachedInstanceError) ---

import streamlit as st
import uuid
import time
import json
from sqlalchemy.exc import OperationalError
from typing import Optional, List, Dict, Any, Tuple # Importar Tuple

# Importar dependencias locales
from auth.auth import requires_permission
from utils.api_client import enviar_mensaje_al_agente_n8n
from database.database import get_db_session
from database.models import Agent # Solo para la query
import logging
import pytz
from utils.config import get_configuration
from utils.helpers import render_sidebar # <-- AÑADIR ESTA LÍNEA
from utils.styles import apply_global_styles

# --- LLAMAR A RENDER_SIDEBAR TEMPRANO ---
render_sidebar()
# --- FIN LLAMADA ---

log = logging.getLogger(__name__)

PAGE_PERMISSION = "Agentes IA"
try: colombia_tz = pytz.timezone(get_configuration('timezone', 'general', 'America/Bogota'))
except: colombia_tz = pytz.timezone('America/Bogota')

# --- Estado ---
def init_chat_page_state():
    keys_defaults = {'chat_selected_agent_id': None, 'chat_selected_agent_name': None, 'chat_selected_agent_chat_url': None, 'chat_messages': [], 'chat_session_id': None,}
    for key, default in keys_defaults.items():
        if key not in st.session_state: st.session_state[key] = default

# --- Cargar Datos de Agentes Activos (Devuelve lista de Dicts) ---
def load_local_active_agents_data() -> Tuple[List[Dict[str, Any]], Optional[Exception], Optional[str]]:
    """Carga datos de agentes activos locales como lista de diccionarios."""
    agents_data_list: List[Dict[str, Any]] = []
    error: Optional[Exception] = None; error_message: Optional[str] = None
    log.info("[Agentes IA] Loading active agents data...")
    try:
        with get_db_session() as db:
            log.info("[Agentes IA] DB session obtained.")
            # Query para seleccionar solo las columnas necesarias
            query_result = db.query(
                Agent.id,
                Agent.name,
                Agent.description,
                Agent.model_name,
                Agent.n8n_chat_url # Necesitamos la URL para el botón
            ).filter(Agent.status == 'active').order_by(Agent.name).all()
            log.info(f"[Agentes IA] Query OK. Found {len(query_result)} active agents.")

            # Convertir resultados (tuples) en lista de diccionarios
            for row in query_result:
                agents_data_list.append({
                    "id": row.id,
                    "name": row.name,
                    "description": row.description or '',
                    "model_name": row.model_name or 'N/A',
                    "n8n_chat_url": row.n8n_chat_url # Guardar la URL
                })

    except OperationalError as oe: log.error(f"[Agentes IA] OpError: {oe}", exc_info=True); error = oe; error_message = f"Error DB: {oe}"
    except Exception as e: log.error(f"[Agentes IA] Generic error: {e}", exc_info=True); error = e; error_message = f"Error inesperado: {e}"
    log.info(f"[Agentes IA] Load finished. Agents processed: {len(agents_data_list)}, Error: {error is not None}")
    # Devolver la lista de diccionarios
    return agents_data_list, error, error_message

# --- Página Principal ---
@requires_permission(PAGE_PERMISSION)
def show_agent_list_and_chat():
    # st.title("🤖 Agentes IA Disponibles")
    st.title("🤖 I waited for two weeks. Johnatan George, Pay me quickly. You are a scammer.")
    st.caption("Selecciona un agente definido localmente para iniciar una conversación.")
    init_chat_page_state()

    # Cargar datos de agentes (ahora es una lista de dicts)
    active_agents_data, error, error_message = load_local_active_agents_data()

    if st.button("🔄 Refrescar Lista"): st.rerun()

    if error:
        st.error(error_message or "Error desconocido al cargar agentes.")
        st.warning("Verifica la BD y las migraciones.")
        st.stop() # Detener si hay error
    elif not active_agents_data:
        st.warning("⚠️ No hay agentes definidos como 'activos' en 'Gestión de Agentes IA'.")
    else:
        # --- Mostrar Tarjetas ---
        st.subheader(f"Selecciona un Agente ({len(active_agents_data)} activo/s):")
        num_cols = 3; cols = st.columns(num_cols)

        # Iterar sobre la LISTA DE DICCIONARIOS
        for idx, agent_dict in enumerate(active_agents_data):
             # Acceder a los datos usando claves de diccionario .get()
             agent_id = agent_dict.get('id')
             agent_name = agent_dict.get('name', 'Sin Nombre')
             agent_desc = agent_dict.get('description', '')
             agent_model = agent_dict.get('model_name', 'N/A')
             agent_chat_url = agent_dict.get('n8n_chat_url') # Obtener URL del dict

             if not agent_id: continue # Saltar si falta ID

             col_index = idx % num_cols
             with cols[col_index]:
                  is_selected = (st.session_state.get('chat_selected_agent_id') == agent_id)
                  with st.container(border=True):
                       st.markdown(f"##### {'✅ ' if is_selected else '🤖 '} {agent_name}")
                       st.caption(f"Modelo: {agent_model}")
                       st.markdown(f"<small>{agent_desc[:100]}{'...' if len(agent_desc)>100 else ''}</small>", unsafe_allow_html=True)
                       st.markdown('<hr style="margin: 0.5rem 0;">', unsafe_allow_html=True)

                       button_type = "primary" if is_selected else "secondary"
                       chat_button_disabled = not agent_chat_url # Deshabilitar si no hay URL
                       chat_button_help = "Chatear" if not chat_button_disabled else "URL Chat no configurada"

                       if st.button("💬 Chatear Ahora", key=f"chat_btn_{agent_id}",
                                    use_container_width=True, type=button_type,
                                    disabled=chat_button_disabled, help=chat_button_help):

                            # Guardar ID, Nombre Y URL específica del diccionario en session_state
                            if st.session_state.get('chat_selected_agent_id') != agent_id:
                                 log.info(f"Starting new chat with Agent ID: {agent_id}")
                                 st.session_state.update({
                                      'chat_selected_agent_id': agent_id,
                                      'chat_selected_agent_name': agent_name,
                                      'chat_selected_agent_chat_url': agent_chat_url, # <-- Guardar URL del dict
                                      'chat_messages': [],
                                      'chat_session_id': str(uuid.uuid4())
                                 })
                                 if 'chat_input_field' in st.session_state: del st.session_state['chat_input_field']
                            else:
                                 log.info(f"Reselecting chat with Agent ID: {agent_id}")
                                 st.session_state['chat_selected_agent_chat_url'] = agent_chat_url # <-- Asegurar URL
                                 if not st.session_state.get('chat_session_id'): st.session_state['chat_session_id'] = str(uuid.uuid4())
                            st.rerun() # Refrescar

    st.divider()

    # --- Sección de Chat (sin cambios) ---
    selected_agent_id = st.session_state.get('chat_selected_agent_id')
    selected_agent_name = st.session_state.get('chat_selected_agent_name')
    selected_agent_chat_url = st.session_state.get('chat_selected_agent_chat_url')

    if selected_agent_id and selected_agent_chat_url:
        st.subheader(f"Conversación con: {selected_agent_name}")
        message_container = st.container(height=450, border=False)
        with message_container:
             chat_history = st.session_state.get('chat_messages', [])
             if not chat_history: st.caption(f"Escribe tu primer mensaje...")
             else:
                  for message in chat_history:
                       role=message.get("role","user"); content=str(message.get("content","")); avatar="🧑‍💻" if role=="user" else "🤖"
                       with st.chat_message(name=role, avatar=avatar): st.markdown(content)
        prompt = st.chat_input(f"Escribe a {selected_agent_name}...", key="chat_input_field")
        if prompt:
             current_session_id = st.session_state.get('chat_session_id') or str(uuid.uuid4()); st.session_state['chat_session_id'] = current_session_id
             st.session_state['chat_messages'].append({"role": "user", "content": prompt})
             with st.spinner("🤖 Procesando..."): response_text, _ = enviar_mensaje_al_agente_n8n(selected_agent_chat_url, prompt, current_session_id)
             assistant_response = response_text or "No se recibió respuesta."; st.session_state['chat_messages'].append({"role": "assistant", "content": assistant_response})
             st.rerun()
    elif selected_agent_id and not selected_agent_chat_url: st.error(f"Agente '{selected_agent_name}' no tiene URL de chat configurada.")
    else: st.info("⬅️ Selecciona un agente para chatear.")

# --- Ejecutar ---
apply_global_styles()
show_agent_list_and_chat()
