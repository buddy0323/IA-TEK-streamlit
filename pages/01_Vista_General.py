# --- pages/01_Vista_General.py (NUEVO - Placeholder con Datos de Ejemplo) ---
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy import func

# Importar decorador de permisos
from auth.auth import requires_permission, check_authentication
from utils.helpers import render_sidebar
from utils.cookies import get_session_cookie
from database.database import get_db_session
from database.models import Agent, Query
from utils.styles import apply_global_styles

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

    # Obtener total de agentes desde la base de datos
    with get_db_session() as db:
        total_agentes = db.query(Agent).count()
        agentes_activos = db.query(Agent).filter(Agent.status == 'active').count()

        # Obtener consultas de hoy y tasa de éxito
        today = datetime.now().date()
        try:
            # Intentar consulta con el nuevo esquema
            consultas_hoy = db.query(Query).filter(
                Query.created_at >= today,
                Query.created_at < today + timedelta(days=1)
            ).count()

            consultas_exitosas_hoy = db.query(Query).filter(
                Query.created_at >= today,
                Query.created_at < today + timedelta(days=1),
                Query.success == True
            ).count()

            tasa_exito_global = (consultas_exitosas_hoy / consultas_hoy * 100) if consultas_hoy > 0 else 0

            # Calcular delta vs ayer
            consultas_ayer = db.query(Query).filter(
                Query.created_at >= today - timedelta(days=1),
                Query.created_at < today
            ).count()
            delta_consultas = consultas_hoy - consultas_ayer

            # Calcular tasa de éxito de ayer
            consultas_exitosas_ayer = db.query(Query).filter(
                Query.created_at >= today - timedelta(days=1),
                Query.created_at < today,
                Query.success == True
            ).count()
            tasa_exito_ayer = (consultas_exitosas_ayer / consultas_ayer * 100) if consultas_ayer > 0 else 0
            delta_tasa = tasa_exito_global - tasa_exito_ayer

        except Exception as e:
            st.error(f"Error al consultar datos: {e}")
            # Valores por defecto en caso de error
            consultas_hoy = 0
            tasa_exito_global = 0
            delta_consultas = 0
            delta_tasa = 0

    with col1:
        st.metric("Agentes Totales", f"{total_agentes} 🤖")
    with col2:
        st.metric("Agentes Activos", f"{agentes_activos} / {total_agentes}", f"{((agentes_activos/total_agentes)*100):.0f}%")
    with col3:
        st.metric("Consultas (Hoy)", f"{consultas_hoy} 💬", f"{delta_consultas:+}")
    with col4:
        st.metric("Tasa Éxito Global", f"{tasa_exito_global:.1f}%", f"{delta_tasa:.1f}%")

    st.markdown("---")

    # --- Gráficos de Ejemplo ---
    st.subheader("Visualizaciones")
    col_chart1, col_chart2 = st.columns(2)

    # Crear datos de ejemplo para gráficos
    # Consultas últimos 7 días
    today = datetime.now().date()
    dates_7d = [today - timedelta(days=i) for i in range(6, -1, -1)]

    queries_7d = []
    for day in dates_7d:
        next_day = day + timedelta(days=1)
        count = db.query(func.count(Query.id)).filter(
            Query.created_at >= day,
            Query.created_at < next_day
        ).scalar()
        queries_7d.append(count)

    df_queries = pd.DataFrame({'Fecha': dates_7d, 'Consultas': queries_7d})

    # Tasa de éxito últimos 7 días
    success_rate_7d = []
    for day in dates_7d:
        next_day = day + timedelta(days=1)
        total = db.query(func.count(Query.id)).filter(
            Query.created_at >= day,
            Query.created_at < next_day
        ).scalar()
        success = db.query(func.count(Query.id)).filter(
            Query.created_at >= day,
            Query.created_at < next_day,
            Query.success == True
        ).scalar()
        rate = (success / total * 100) if total > 0 else 0
        success_rate_7d.append(rate)

    df_success = pd.DataFrame({'Fecha': dates_7d, 'Tasa Éxito (%)': success_rate_7d})

    # Get usage data from the db: number of queries per agent name
    usage_data = (
        db.query(Agent.name, func.count(Query.id))
        .join(Query, Query.agent_id == Agent.id)
        .group_by(Agent.name)
        .order_by(Agent.name)
        .all()
    )

    # Unzip the results
    agent_names = [row[0] for row in usage_data]
    agent_usage = [row[1] for row in usage_data]

    # Create the DataFrame
    df_usage = pd.DataFrame({'Agente': agent_names, 'Consultas': agent_usage})

    with col_chart1:
        st.markdown("##### Consultas en Últimos 7 Días")
        fig_line = px.line(df_queries, x='Fecha', y='Consultas', markers=True,
                           labels={'Consultas': 'Nº Consultas'})
        fig_line.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=400)
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
        # Get the last 24 hours of data for successful queries only
        start_time = (datetime.now() - timedelta(hours=23)).replace(minute=0, second=0, microsecond=0)
        end_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        resp_data = db.query(Query.created_at, Query.response_time_ms).filter(
            Query.created_at >= start_time,
            Query.success == True
        ).order_by(Query.created_at).all()

        # Unpack the results
        hours = [row[0] for row in resp_data]
        avg_resp_time = [row[1] for row in resp_data]

        df_resp = pd.DataFrame({'Hora': pd.to_datetime(hours), 'Tiempo Respuesta (ms)': avg_resp_time})
        if not df_resp.empty:
            df_resp.set_index('Hora', inplace=True)
            # Group by hour
            df_hour = df_resp.resample('H').mean()
            # Create a complete range of hours for the last 24 hours
            all_hours = pd.date_range(start=start_time, end=end_time, freq='H')
            df_hour = df_hour.reindex(all_hours)
            df_hour = df_hour.reset_index().rename(columns={'index': 'Hora'})
            # Create a text label column: show value only if not NaN and > 0, else empty string
            df_hour['label'] = df_hour['Tiempo Respuesta (ms)'].apply(
                lambda x: f'{x:.0f}' if pd.notnull(x) and x > 0 else ''
            )
            fig_resp_area = px.area(
                df_hour,
                x='Hora',
                y='Tiempo Respuesta (ms)',
                markers=True,
                text='label',
                line_shape='linear',
                color_discrete_sequence=['#1f77b4']
            )
            fig_resp_area.update_traces(
                texttemplate='%{text}',
                textposition='top center',
                mode='lines+markers+text',
                fill='tozeroy'
            )
            fig_resp_area.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=350,
                xaxis_tickformat='%H:%M\n%b %d',
                xaxis_title='Hora',
                yaxis_range=[0, None],
                yaxis=dict(tickformat='.0f'),
                showlegend=False
            )
            st.plotly_chart(fig_resp_area, use_container_width=True)
        else:
            st.info("No hay datos de respuesta exitosos en las últimas 24 horas.")

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
    apply_global_styles()
    render_sidebar()
    show_general_view_placeholder()
else:
    st.stop()
