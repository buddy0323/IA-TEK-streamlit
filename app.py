# --- app.py ---
import streamlit as st
import time
import os
from sqlalchemy.exc import OperationalError

# Importaciones locales revisadas y organizadas
from auth.auth import init_session_state, check_authentication, show_login_page, logout
from database.database import engine, apply_sqlite_migrations
from database.models import Base
from utils.styles import apply_global_styles, show_navbar
from utils.helpers import render_sidebar # Importar la función del sidebar
from utils.config import get_configuration # Importar aquí para set_page_config
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# --- Configuración Inicial de la Página ---
APP_TITLE_DEFAULT = "IA-AMCO Dashboard"
APP_ICON_DEFAULT = "🤖"
try:
    app_title = get_configuration('dashboard_name', 'general', APP_TITLE_DEFAULT) or APP_TITLE_DEFAULT
    app_icon_url = get_configuration('logo_url', 'general', None)
    app_icon = app_icon_url if app_icon_url and isinstance(app_icon_url, str) and app_icon_url.startswith('http') else APP_ICON_DEFAULT
except OperationalError:
    print("WARN: Database not ready for config read during set_page_config. Using defaults.")
    app_title = APP_TITLE_DEFAULT; app_icon = APP_ICON_DEFAULT
except Exception as e:
    print(f"ERROR reading config for page setup: {e}. Using defaults.")
    app_title = APP_TITLE_DEFAULT; app_icon = APP_ICON_DEFAULT

st.set_page_config(
    page_title=app_title,
    page_icon=app_icon,
    layout="wide",
    initial_sidebar_state="expanded"
    # --- LÍNEA 'show_default_navigation=False' ELIMINADA ---
)

# --- Aplicar Migraciones (Tu código existente sin cambios) ---
MIGRATION_APPLIED_FLAG = '.migration_applied_on_server_start'
if not os.path.exists(MIGRATION_APPLIED_FLAG):
    print("Attempting to apply database migrations (first run in this session)...")
    try:
        apply_sqlite_migrations(engine, Base, "database/migrations")
        print("Migrations check/application process finished.")
        with open(MIGRATION_APPLIED_FLAG, 'w') as f: f.write(f'Applied at: {time.time()}')
        print(f"Migration flag '{MIGRATION_APPLIED_FLAG}' created.")
    except OperationalError as oe:
         print(f"!!! OPERATIONAL ERROR during migrations: {oe}")
         st.error(f"Error crítico DB: {oe}. Verifique config/permisos.")
         st.stop()
    except Exception as e:
        print(f"!!! FATAL ERROR applying migrations: {e}")
        st.error("Error crítico inicializando BD. Revise logs.")
        st.stop()
else:
     print("Migrations flag found. Skipping migration check.")

# --- Lógica Principal (Tu código existente sin cambios) ---
init_session_state()
try: apply_global_styles()
except Exception as e_style: log.error(f"Error styles: {e_style}", exc_info=True); st.error("Error aplicando estilos.")

is_authenticated = check_authentication()

if not is_authenticated:
    show_login_page()
    st.stop()
else:
    # --- Usuario Autenticado ---
    show_navbar()
    render_sidebar() # Llama a la función que genera el sidebar correcto

    # El contenido principal se renderiza automáticamente desde la página seleccionada

# --- Fin del Script app.py ---