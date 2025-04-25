import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from collections import Counter
import re
import pytz # Importar pytz directamente

# Importar dependencias locales
from auth.auth import requires_permission # Decorador
from utils.config import get_configuration # Para obtener timezone
from database.database import get_db_session, engine # Necesitamos engine para pd.read_sql
from database.models import Query, Agent # Modelos
from utils.helpers import render_sidebar # <-- AÑADIR ESTA LÍNEA

# --- LLAMAR A RENDER_SIDEBAR TEMPRANO ---
render_sidebar()
# --- FIN LLAMADA ---

# Permiso requerido para acceder a esta página
PAGE_PERMISSION = "Análisis de Consultas"

# Obtener zona horaria configurada (con fallback)
try:
    TIMEZONE_STR = get_configuration('timezone', 'general', 'America/Bogota')
    colombia_tz = pytz.timezone(TIMEZONE_STR)
except pytz.exceptions.UnknownTimeZoneError:
    print(f"WARN: Timezone '{TIMEZONE_STR}' not found, using 'America/Bogota'.")
    colombia_tz = pytz.timezone('America/Bogota')
except Exception as e:
     print(f"ERROR reading timezone config: {e}. Using 'America/Bogota'.")
     colombia_tz = pytz.timezone('America/Bogota')


@requires_permission(PAGE_PERMISSION)
def show_query_analysis_page():
    """Muestra la página de Análisis de Consultas con filtros y gráficos."""
    st.title("🔍 Análisis de Consultas")
    st.caption("Explora patrones y tendencias en las interacciones con los agentes.")

    # --- Filtros ---
    with st.expander("📊 Aplicar Filtros para Análisis", expanded=True):
        col_f1, col_f2 = st.columns(2)

        # Cargar agentes para filtro
        try:
            with get_db_session() as db:
                agents = db.query(Agent.id, Agent.name).order_by(Agent.name).all()
                agent_options_display = {"Todos los Agentes": None}
                agent_options_display.update({agent.name: agent.id for agent in agents})
        except Exception as e:
            st.error(f"Error cargando lista de agentes para filtro: {e}")
            agent_options_display = {"Todos los Agentes": None}

        with col_f1:
            selected_agent_name = st.selectbox(
                "Analizar Agente:",
                options=list(agent_options_display.keys()),
                index=0, # Default 'Todos'
                key="analysis_agent_filter"
            )
            selected_agent_id = agent_options_display[selected_agent_name]

        with col_f2:
            # Filtro de fecha
            today = datetime.now(colombia_tz).date()
            default_start_date = today - timedelta(days=30) # Default último mes
            date_range = st.date_input(
                "Seleccionar Rango de Fechas:",
                value=(default_start_date, today),
                min_value=today - timedelta(days=365*2), # Limitar a 2 años
                max_value=today,
                key="analysis_date_range"
            )
            # Procesar rango de fechas
            start_date_dt, end_date_dt = None, None
            if date_range and len(date_range) == 2:
                start_date_dt = datetime.combine(date_range[0], datetime.min.time(), tzinfo=colombia_tz)
                end_date_dt = datetime.combine(date_range[1] + timedelta(days=1), datetime.min.time(), tzinfo=colombia_tz)
            else: # Fallback
                 start_date_dt = datetime.combine(default_start_date, datetime.min.time(), tzinfo=colombia_tz)
                 end_date_dt = datetime.combine(today + timedelta(days=1), datetime.min.time(), tzinfo=colombia_tz)

    st.divider()

    # --- Cargar Datos Filtrados en DataFrame ---
    df_queries = pd.DataFrame() # Inicializar DataFrame vacío
    try:
        with get_db_session() as db:
            # Construir la consulta base SQLAlchemy
            query_base = db.query(
                Query.created_at,
                Query.success,
                Query.response_time_ms,
                Query.query_text,
                Agent.name.label('agent_name') # Etiquetar para nombre de columna claro
            ).join(Agent, Query.agent_id == Agent.id) # Asegurar JOIN explícito

            # Aplicar filtros a la consulta SQLAlchemy
            if start_date_dt and end_date_dt:
                query_base = query_base.filter(
                    Query.created_at >= start_date_dt,
                    Query.created_at < end_date_dt
                )
            if selected_agent_id is not None:
                query_base = query_base.filter(Query.agent_id == selected_agent_id)

            # Ejecutar consulta y cargar directamente en Pandas DataFrame
            # Usar db.bind (el engine) para la conexión de Pandas
            df_queries = pd.read_sql(query_base.statement, db.bind)

        if df_queries.empty:
             st.info("No hay datos de consultas para el período y filtros seleccionados.")
             st.stop() # No continuar si no hay datos

        # --- Procesamiento Post-Carga del DataFrame ---
        # Convertir created_at a tipo datetime con zona horaria correcta
        # pd.read_sql a veces maneja esto, pero mejor asegurarse
        if not pd.api.types.is_datetime64_any_dtype(df_queries['created_at']):
             df_queries['created_at'] = pd.to_datetime(df_queries['created_at'], errors='coerce')
        # Asegurar timezone (si viene sin él, asumir UTC y convertir a Colombia TZ)
        if df_queries['created_at'].dt.tz is None:
             df_queries['created_at'] = df_queries['created_at'].dt.tz_localize('UTC').dt.tz_convert(colombia_tz)
        else:
             # Si ya tiene timezone, solo convertir al de Colombia
             df_queries['created_at'] = df_queries['created_at'].dt.tz_convert(colombia_tz)

        # Crear columna binaria para éxito (manejar posibles Nones o valores inesperados)
        df_queries['is_success'] = df_queries['success'].apply(lambda x: 1 if x == 1 else 0)
        # Limpiar response_time_ms (convertir a numérico, manejar errores, quitar negativos)
        df_queries['response_time_ms'] = pd.to_numeric(df_queries['response_time_ms'], errors='coerce')
        df_queries = df_queries.dropna(subset=['response_time_ms']) # Quitar filas donde no se pudo convertir
        df_queries = df_queries[df_queries['response_time_ms'] > 0] # Mantener solo tiempos positivos

    except Exception as e:
        st.error(f"Error al cargar o procesar datos para análisis: {e}")
        # st.exception(e) # Descomentar para debug
        st.stop() # Detener si falla la carga/procesamiento

    # --- Realizar y Mostrar Análisis ---
    st.subheader("Resultados del Análisis")

    # Layout para gráficos
    col_a1, col_a2 = st.columns(2)

    # 1. Volumen de Consultas por Día
    with col_a1:
        st.markdown("📈 **Volumen Diario de Consultas**")
        try:
            daily_volume = df_queries.set_index('created_at').resample('D').size()
            daily_volume = daily_volume[daily_volume > 0] # Mostrar solo días con actividad
            if not daily_volume.empty:
                 fig_volume = px.line(
                      daily_volume, markers=True,
                      labels={'created_at': 'Fecha', 'value': 'Nº Consultas'},
                      # title="Volumen Diario de Consultas" # Título ya está en markdown
                 )
                 fig_volume.update_layout(showlegend=False, margin=dict(t=5, b=5, l=5, r=5), height=350)
                 fig_volume.update_traces(line_color='#1f77b4') # Azul Plotly
                 st.plotly_chart(fig_volume, use_container_width=True)
            else:
                 st.caption("No hay datos de volumen para mostrar.")
        except Exception as e:
            st.warning(f"No se pudo generar gráfico de volumen: {e}")

    # 2. Tasa de Éxito por Día
    with col_a2:
         st.markdown("📊 **Tasa de Éxito Diario (%)**")
         try:
             # Calcular tasa de éxito diaria (requiere 'is_success' creada antes)
             daily_success_rate = df_queries.set_index('created_at').resample('D')['is_success'].mean() * 100
             daily_success_rate = daily_success_rate.dropna() # Quitar días sin datos
             if not daily_success_rate.empty:
                 fig_success = px.line(
                      daily_success_rate, markers=True, range_y=[0, 105],
                      labels={'created_at': 'Fecha', 'value': 'Tasa Éxito (%)'},
                      # title="Tasa de Éxito Diario (%)"
                 )
                 fig_success.update_layout(showlegend=False, margin=dict(t=5, b=5, l=5, r=5), height=350)
                 fig_success.update_traces(line_color='#2ca02c') # Verde Plotly
                 st.plotly_chart(fig_success, use_container_width=True)
             else:
                 st.caption("No hay datos de tasa de éxito para mostrar.")
         except Exception as e:
            st.warning(f"No se pudo generar gráfico de tasa de éxito: {e}")

    st.divider()

    # 3. Distribución del Tiempo de Respuesta
    st.markdown("⏱️ **Distribución del Tiempo de Respuesta**")
    try:
        valid_response_times = df_queries['response_time_ms'] # Ya filtrado Nones/negativos
        if not valid_response_times.empty:
             avg_time = valid_response_times.mean()
             median_time = valid_response_times.median()
             p90_time = valid_response_times.quantile(0.9)

             fig_resp_time = px.histogram(
                  valid_response_times, nbins=40, # Ajustar número de barras
                  labels={'value': 'Tiempo Respuesta (ms)', 'count': 'Frecuencia'},
                  opacity=0.75, title="Histograma de Tiempos de Respuesta (ms)"
             )
             fig_resp_time.add_vline(x=avg_time, line_dash="dash", line_color="red", annotation_text=f"Prom: {avg_time:.0f} ms")
             fig_resp_time.add_vline(x=median_time, line_dash="dot", line_color="green", annotation_text=f"Med: {median_time:.0f} ms")
             fig_resp_time.add_vline(x=p90_time, line_dash="longdashdot", line_color="purple", annotation_text=f"P90: {p90_time:.0f} ms")

             fig_resp_time.update_layout(margin=dict(t=30, b=10, l=10, r=10), height=400)
             st.plotly_chart(fig_resp_time, use_container_width=True)
             st.caption(f"Estadísticas: Promedio={avg_time:.0f}ms, Mediana={median_time:.0f}ms, Percentil 90={p90_time:.0f}ms")
        else:
             st.caption("No hay datos válidos de tiempo de respuesta para mostrar.")
    except Exception as e:
        st.warning(f"No se pudo generar histograma de tiempo de respuesta: {e}")

    st.divider()

    # 4. Análisis Básico de Texto (Palabras más frecuentes)
    st.markdown("📝 **Análisis Básico de Texto de Consultas**")
    st.caption("Muestra las palabras más frecuentes en las consultas (excluyendo palabras comunes). Análisis muy básico.")
    try:
         all_text = " ".join(df_queries['query_text'].astype(str).str.lower())
         # Limpieza básica: quitar caracteres no alfanuméricos (excepto espacios)
         # Podría mejorarse para manejar acentos, etc.
         cleaned_text = re.sub(r'[^\w\s]', '', all_text, flags=re.UNICODE)
         words = cleaned_text.split()

         # Lista básica de stopwords en español (se puede expandir o usar NLTK/spaCy)
         stopwords_es = set([
              'de', 'la', 'que', 'el', 'en', 'y', 'a', 'los', 'del', 'se', 'las', 'por', 'un',
              'para', 'con', 'no', 'una', 'su', 'al', 'lo', 'como', 'más', 'pero', 'sus',
              'le', 'ha', 'me', 'si', 'sin', 'sobre', 'este', 'ya', 'entre', 'cuando',
              'todo', 'esta', 'ser', 'son', 'dos', 'también', 'fue', 'habia', 'era',
              'muy', 'hasta', 'desde', 'nos', 'mi', 'mucho', 'quien', 'yo', 'eso', 'es',
              'consulta', 'quiero', 'saber', 'necesito', 'informacion', 'puede', 'ayudar',
              # Añadir términos muy genéricos del dominio si es necesario
         ])

         # Filtrar palabras cortas y stopwords
         filtered_words = [word for word in words if word not in stopwords_es and len(word) > 3]

         if filtered_words:
              word_counts = Counter(filtered_words)
              most_common_words = word_counts.most_common(20) # Top 20

              df_words = pd.DataFrame(most_common_words, columns=['Palabra', 'Frecuencia'])
              fig_words = px.bar(
                   df_words.sort_values('Frecuencia', ascending=True), # Ordenar para visualización
                   x='Frecuencia', y='Palabra', orientation='h',
                   # title="Top 20 Palabras Más Frecuentes",
                   labels={'Frecuencia': 'Nº Apariciones', 'Palabra': 'Palabra'}
              )
              fig_words.update_layout(margin=dict(t=5, b=5, l=5, r=5), height=450)
              st.plotly_chart(fig_words, use_container_width=True)
         else:
              st.caption("No se encontraron palabras significativas para analizar después de filtrar.")

    except Exception as text_e:
         st.warning(f"No se pudo realizar el análisis básico de texto: {text_e}")

# --- Ejecutar la Página ---
show_query_analysis_page()
