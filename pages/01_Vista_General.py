# --- pages/01_Vista_General.py (NUEVO - Placeholder con Datos de Ejemplo) ---
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Importar decorador de permisos
from auth.auth import requires_permission, check_authentication
from utils.helpers import render_sidebar
from utils.cookies import get_session_cookie

# Permiso requerido para esta página
PAGE_PERMISSION = "Vista General"

@requires_permission(PAGE_PERMISSION)
def show_general_view_placeholder():
    """Muestra la página de Vista General con datos y gráficos de ejemplo."""

    st.title("📊 Vista General del Dashboard")
    st.caption(f"Resumen y métricas clave. Fecha actual: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    st.markdown("---")

    # --- Métricas Clave (Ejemplo) ---
    st.subheader("Métricas Clave")
    col1, col2, col3, col4 = st.columns(4)

    # Simular datos
    total_agentes = 15
    agentes_activos = 12
    consultas_hoy = np.random.randint(80, 250)
    tasa_exito_global = np.random.uniform(85.0, 98.0)

    with col1:
        st.metric("Agentes Totales", f"{total_agentes} 🤖")
    with col2:
        st.metric("Agentes Activos", f"{agentes_activos} / {total_agentes}", f"{((agentes_activos/total_agentes)*100):.0f}%")
    with col3:
        delta_consultas = consultas_hoy - np.random.randint(70, 200) # Simular delta vs ayer
        st.metric("Consultas (Hoy)", f"{consultas_hoy} 💬", f"{delta_consultas:+}")
    with col4:
        delta_tasa = tasa_exito_global - np.random.uniform(84.0, 97.0) # Simular delta vs semana pasada
        st.metric("Tasa Éxito Global", f"{tasa_exito_global:.1f}%", f"{delta_tasa:.1f}%")

    st.markdown("---")

    # --- Gráficos de Ejemplo ---
    st.subheader("Visualizaciones")
    col_chart1, col_chart2 = st.columns(2)

    # Crear datos de ejemplo para gráficos
    # Consultas últimos 7 días
    today = datetime.now().date()
    dates_7d = [today - timedelta(days=i) for i in range(6, -1, -1)]
    queries_7d = np.random.randint(50, 300, size=7)
    df_queries = pd.DataFrame({'Fecha': dates_7d, 'Consultas': queries_7d})

    # Tasa de éxito últimos 7 días
    success_rate_7d = np.random.uniform(80.0, 99.0, size=7)
    df_success = pd.DataFrame({'Fecha': dates_7d, 'Tasa Éxito (%)': success_rate_7d})

    # Distribución de uso por agente (Pie Chart)
    agent_names = [f"Agente {chr(65+i)}" for i in range(5)] # Agente A, B, C...
    agent_usage = np.random.randint(50, 500, size=5)
    df_usage = pd.DataFrame({'Agente': agent_names, 'Consultas': agent_usage})


    with col_chart1:
        st.markdown("##### Consultas en Últimos 7 Días")
        fig_line = px.line(df_queries, x='Fecha', y='Consultas', markers=True,
                           labels={'Consultas': 'Nº Consultas'})
        fig_line.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=350)
        st.plotly_chart(fig_line, use_container_width=True)

        st.markdown("##### Tasa de Éxito en Últimos 7 Días")
        fig_success_line = px.line(df_success, x='Fecha', y='Tasa Éxito (%)', markers=True, range_y=[0, 105])
        fig_success_line.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=350)
        fig_success_line.update_traces(line_color='green')
        st.plotly_chart(fig_success_line, use_container_width=True)

    with col_chart2:
        st.markdown("##### Distribución de Consultas por Agente (Ejemplo)")
        fig_pie = px.pie(df_usage, values='Consultas', names='Agente', hole=0.4,
                         title=" ") # Título vacío, usamos markdown arriba
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(showlegend=True, margin=dict(t=20, b=20, l=20, r=20), height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("##### Tiempo de Respuesta Promedio (Simulado)")
        # Simular tiempos de respuesta por hora (últimas 24h)
        hours = pd.to_datetime([datetime.now() - timedelta(hours=i) for i in range(23, -1, -1)])
        avg_resp_time = np.random.uniform(500, 3500, size=24) # ms
        df_resp = pd.DataFrame({'Hora': hours, 'Tiempo Respuesta (ms)': avg_resp_time})
        fig_resp_area = px.area(df_resp, x='Hora', y='Tiempo Respuesta (ms)', markers=True)
        fig_resp_area.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=310) # Ajustar altura
        st.plotly_chart(fig_resp_area, use_container_width=True)

    st.markdown("---")
    st.caption("Nota: Todos los datos y gráficos en esta página son de ejemplo y solo para demostración visual.")


# --- Ejecutar la Página ---
# First check for session cookie
cookie_data = get_session_cookie()
if cookie_data:
    # Restore session state from cookie
    for key in ['authenticated', 'username', 'user_id', 'role_name', 'permissions']:
        if key in cookie_data:
            st.session_state[key] = cookie_data[key]
    if 'permissions' in cookie_data:
        st.session_state['permissions'] = set(cookie_data['permissions'])

# Always render sidebar and show content if authenticated
if st.session_state.get('authenticated', False):
    render_sidebar()
    show_general_view_placeholder()
else:
    st.stop()
