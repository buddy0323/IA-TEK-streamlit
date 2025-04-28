import streamlit as st
import re
from typing import Optional

# Importaciones necesarias para la función del sidebar
from utils.config import get_configuration
from auth.auth import show_login_page, logout # Importar función logout
from auth.auth import check_authentication
import logging

log = logging.getLogger(__name__)

# --- Mapeo de Permisos a Archivos de Página ---
# Clave: Nombre exacto del permiso (como en la BD/Roles)
# Valor: Ruta relativa del archivo .py en la carpeta pages/
PAGE_PERMISSION_MAP = {
    "Vista General": "pages/01_Vista_General.py",
    "Gestión de agentes IA": "pages/02_Gestion_Agentes_IA.py",
    "Agentes IA": "pages/03_Agentes_IA.py",
    "Entrenar": "pages/04_Entrenar.py",
    "Monitoreo": "pages/05_Monitoreo.py",
    "Historial de Conversaciones": "pages/06_Historial_Conversaciones.py",
    "Análisis de Consultas": "pages/07_Analisis_Consultas.py",
    "Gestión de Usuarios": "pages/08_Gestion_Usuarios.py",
    "Configuración": "pages/09_Configuracion.py",
    "Mi Perfil": "pages/10_Mi_Perfil.py",
    "Roles": "pages/11_Roles.py",
}

# --- Funciones existentes ---
def is_valid_email(email: Optional[str]) -> bool:
    # ... (tu código existente) ...
    if not email:
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.fullmatch(pattern, email) is not None

def show_dev_placeholder(page_title: str):
    # ... (tu código existente) ...
    st.warning(f"🚧 La sección **'{page_title}'** aún está en desarrollo.", icon="🛠️")
    st.markdown("Las funcionalidades principales para esta área se implementarán próximamente.")
    st.info("Si tienes ideas o requisitos específicos para esta sección, por favor comunícalos.")


# --- NUEVA FUNCIÓN PARA RENDERIZAR SIDEBAR ---
def render_sidebar():
    """
    Renderiza el contenido completo del sidebar, incluyendo logo,
    enlaces de página filtrados por permisos, información de usuario
    y botón de logout.
    """
    with st.sidebar:
        # 1. Mostrar logo si está configurado
        logo_sidebar_url = get_configuration('logo_url', 'general', None)
        if logo_sidebar_url:
            st.image(logo_sidebar_url)
            st.divider()

        st.markdown("### Menú Principal")

        # 2. Generar enlaces de página filtrados
        user_permissions = st.session_state.get('permissions', set())
        log.debug(f"Rendering sidebar for user '{st.session_state.get('username')}' with permissions: {user_permissions}")

        # Obtener el orden de las páginas basado en los nombres de archivo
        # (Asume que los números en los nombres de archivo definen el orden deseado)
        # Creamos una lista ordenada de tuplas (permiso, ruta) basada en PAGE_PERMISSION_MAP
        # y la ordenamos por la ruta (que contiene el número)
        ordered_pages = sorted(PAGE_PERMISSION_MAP.items(), key=lambda item: item[1])

        # Iterar sobre las páginas ordenadas y mostrar enlaces si hay permiso
        for permission_name, page_path in ordered_pages:
            if permission_name in user_permissions:
                # Extraer el nombre legible del permiso (o del archivo si se prefiere)
                page_label = permission_name # Usar el nombre del permiso como etiqueta
                # Usar st.page_link para crear la navegación
                st.page_link(page_path, label=page_label, icon=None) # Puedes elegir iconos
                log.debug(f"  - Allowed: {page_label} ({page_path})")
            else:
                 log.debug(f"  - Denied: {permission_name} ({page_path})")

        st.markdown("---") # Separador antes de info de usuario

        # 3. Mostrar información del usuario logueado
        st.markdown(f"👤 **Usuario:** {st.session_state.get('username', 'N/A')}")
        st.markdown(f"🎭 **Rol:** {st.session_state.get('role_name', 'N/A')}")

        # 4. Botón de Cerrar Sesión
        if st.button("🚪 Cerrar Sesión", key="logout_sidebar_central", use_container_width=True):
            # Manually clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            # Optionally clear cookies if you use them
            try:
                from utils.cookies import clear_session_cookie
                clear_session_cookie()
            except Exception:
                pass
            # Show the login page immediately
            st.switch_page("app.py")