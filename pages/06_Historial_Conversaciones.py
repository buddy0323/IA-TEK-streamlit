import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz # Importar pytz directamente para obtener la zona horaria

# Importar dependencias locales
from auth.auth import requires_permission # Decorador
from utils.config import get_configuration # Para obtener timezone configurada
from database.database import get_db_session
from database.models import Query, Agent # Modelos necesarios
from utils.helpers import render_sidebar # <-- AÑADIR ESTA LÍNEA

# --- LLAMAR A RENDER_SIDEBAR TEMPRANO ---
render_sidebar()
# --- FIN LLAMADA ---

# Permiso requerido para acceder a esta página
PAGE_PERMISSION = "Historial de Conversaciones"

# Obtener zona horaria configurada (con fallback)
try:
    TIMEZONE_STR = get_configuration('timezone', 'general', 'America/Bogota')
    colombia_tz = pytz.timezone(TIMEZONE_STR)
except pytz.exceptions.UnknownTimeZoneError:
    print(f"WARN: Timezone '{TIMEZONE_STR}' not found, using 'America/Bogota'.")
    colombia_tz = pytz.timezone('America/Bogota')

@requires_permission(PAGE_PERMISSION)
def show_conversation_history_page():
    """Muestra la página de Historial de Conversaciones con filtros."""
    st.title("📜 Historial de Conversaciones")
    st.caption("Revisa y filtra las interacciones pasadas con los agentes IA.")

    # --- Filtros (Agrupados en un Expander) ---
    with st.expander("🔍 Aplicar Filtros", expanded=True):
        col_f1, col_f2, col_f3 = st.columns(3)

        # Cargar agentes para el filtro
        try:
            with get_db_session() as db:
                agents = db.query(Agent.id, Agent.name).order_by(Agent.name).all()
                agent_options_display = {"Todos los Agentes": None} # Opción default
                agent_options_display.update({agent.name: agent.id for agent in agents})
        except Exception as e:
            st.error(f"Error cargando lista de agentes para filtro: {e}")
            agent_options_display = {"Todos los Agentes": None} # Fallback

        with col_f1:
            # Filtro por Agente
            selected_agent_name = st.selectbox(
                "Filtrar por Agente:",
                options=list(agent_options_display.keys()),
                index=0, # Default 'Todos'
                key="hist_agent_filter"
            )
            selected_agent_id = agent_options_display[selected_agent_name]

        with col_f2:
            # Filtro de Fecha
            today = datetime.now(colombia_tz).date()
            default_start_date = today - timedelta(days=7)
            date_range = st.date_input(
                "Rango de Fechas:",
                value=(default_start_date, today), # Default últimos 7 días
                min_value=today - timedelta(days=365*2), # Limitar a 2 años atrás
                max_value=today,
                key="hist_date_range"
            )
            # Procesar rango de fechas seleccionado
            start_date_dt = None
            end_date_dt = None
            if date_range and len(date_range) == 2:
                # Convertir a datetime con timezone al inicio del día y fin del día
                start_date_dt = datetime.combine(date_range[0], datetime.min.time(), tzinfo=colombia_tz)
                # Fin del día: añadir 1 día y restar 1 microsegundo, o simplemente ir al inicio del día siguiente
                end_date_dt = datetime.combine(date_range[1] + timedelta(days=1), datetime.min.time(), tzinfo=colombia_tz)
            else:
                # Fallback si el date_input no devuelve 2 fechas
                start_date_dt = datetime.combine(default_start_date, datetime.min.time(), tzinfo=colombia_tz)
                end_date_dt = datetime.combine(today + timedelta(days=1), datetime.min.time(), tzinfo=colombia_tz)


        with col_f3:
            # Filtro por Éxito/Fallo
            success_filter_options = {"Todos los Resultados": None, "Éxito": 1, "Fallo": 0}
            selected_success_label = st.selectbox(
                "Filtrar por Resultado:",
                options=list(success_filter_options.keys()),
                index=0, # Default 'Todos'
                key="hist_success_filter"
            )
            selected_success_value = success_filter_options[selected_success_label]

    st.divider()

    # --- Cargar y Mostrar Historial ---
    st.subheader("Conversaciones Registradas")

    try:
        with get_db_session() as db:
            # Query base, ordenando por más reciente
            query_builder = db.query(Query).join(Agent).order_by(Query.created_at.desc())

            # Aplicar filtros
            if start_date_dt and end_date_dt:
                # Asegurarse que las fechas de la DB (que tienen TZ) se comparen correctamente
                query_builder = query_builder.filter(
                    Query.created_at >= start_date_dt,
                    Query.created_at < end_date_dt # Menor que el inicio del día siguiente
                )

            if selected_agent_id is not None:
                query_builder = query_builder.filter(Query.agent_id == selected_agent_id)

            if selected_success_value is not None:
                 # Asumiendo 1 para éxito, 0 para fallo en la BD
                 query_builder = query_builder.filter(Query.success == selected_success_value)

            # Limitar resultados para evitar sobrecarga (paginación sería ideal para muchos datos)
            RESULT_LIMIT = 150
            history_entries = query_builder.limit(RESULT_LIMIT).all()

        if history_entries:
            # Preparar datos para el DataFrame
            history_data = []
            for entry in history_entries:
                # Formatear fecha/hora con zona horaria
                fecha_hora = entry.created_at.astimezone(colombia_tz).strftime('%Y-%m-%d %H:%M:%S') if entry.created_at else 'N/A'
                # Truncar texto largo
                consulta_trunc = (entry.query_text[:80] + '...') if entry.query_text and len(entry.query_text) > 80 else (entry.query_text or '')
                respuesta_trunc = (entry.response_text[:80] + '...') if entry.response_text and len(entry.response_text) > 80 else (entry.response_text or 'N/A')
                # Icono y texto para éxito
                exito_display = "✅ Sí" if entry.success == 1 else ("❌ No" if entry.success == 0 else "❓")

                history_data.append({
                     "Fecha / Hora": fecha_hora,
                     "Agente": entry.agent.name if entry.agent else 'Desconocido',
                     "Consulta": consulta_trunc,
                     "Respuesta": respuesta_trunc,
                     "Éxito": exito_display,
                     "T. Resp (ms)": int(entry.response_time_ms) if entry.response_time_ms is not None else 'N/A',
                     # Podría añadirse "Session ID" si es relevante: entry.session_id
                 })

            # Configurar columnas para el DataFrame (opcional, para orden y nombres)
            column_config = {
                "Fecha / Hora": st.column_config.DatetimeColumn(format="YYYY-MM-DD HH:mm:ss"),
                "T. Resp (ms)": st.column_config.NumberColumn(format="%d ms"),
                # Podríamos definir anchos si fuera necesario, pero es complejo en st.dataframe
            }

            # Mostrar DataFrame
            st.dataframe(
                pd.DataFrame(history_data),
                use_container_width=True,
                hide_index=True,
                column_config=column_config # Aplicar configuración de columnas
                )

            if len(history_entries) >= RESULT_LIMIT:
                 st.caption(f"ℹ️ Mostrando los últimos {RESULT_LIMIT} registros que coinciden con los filtros. Para ver registros más antiguos, ajuste el rango de fechas.")
                 # TODO: Considerar implementar paginación si el volumen de datos es muy alto.
        else:
            st.info("No se encontraron registros de conversaciones para los filtros seleccionados.")

    except Exception as e:
        st.error(f"Ocurrió un error al cargar el historial de conversaciones: {e}")
        # st.exception(e) # Descomentar para ver traceback completo en debug

# --- Ejecutar la Página ---
show_conversation_history_page()
