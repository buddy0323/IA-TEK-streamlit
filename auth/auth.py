# --- auth/auth.py (CORREGIDO - Redirección con st.switch_page) ---

import streamlit as st
import hashlib
from datetime import datetime, timedelta
import re
import pytz
import uuid
import time
from sqlalchemy.orm import joinedload
from typing import Optional, Dict, Any, Tuple, Set # Añadir Set

# Importar desde los nuevos módulos
from database.database import get_db_session
from database.models import User, Role
from utils.config import get_configuration
from utils.styles import get_login_page_style
import logging # Añadir logging

log = logging.getLogger(__name__)

# --- Constantes y Configuración (Sin cambios) ---
try:
    DEFAULT_TIMEZONE = get_configuration('timezone', 'general', 'America/Bogota')
    colombia_tz = pytz.timezone(DEFAULT_TIMEZONE if DEFAULT_TIMEZONE else 'America/Bogota')
except Exception as e:
    log.warning(f"Failed getting/setting timezone config: {e}. Using America/Bogota")
    colombia_tz = pytz.timezone('America/Bogota')

# --- Funciones de Contraseña (Sin cambios) ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_security_config_values():
    defaults = { 'password_min_length': '8', 'password_require_special': 'True', 'password_require_numbers': 'True', 'password_require_uppercase': 'True', 'session_timeout': '60' }
    config = {}
    try:
        with get_db_session() as db:
            for key in defaults: config[key] = get_configuration(key, category='security', default=defaults[key], db_session=db)
    except Exception as e: log.error(f"Error reading security config: {e}"); config = defaults.copy()
    try: # Conversión
        config['password_min_length'] = max(4, int(config.get('password_min_length', defaults['password_min_length'])))
        config['password_require_special'] = str(config.get('password_require_special', defaults['password_require_special'])).lower() == 'true'
        config['password_require_numbers'] = str(config.get('password_require_numbers', defaults['password_require_numbers'])).lower() == 'true'
        config['password_require_uppercase'] = str(config.get('password_require_uppercase', defaults['password_require_uppercase'])).lower() == 'true'
        config['session_timeout'] = max(5, int(config.get('session_timeout', defaults['session_timeout'])))
    except (ValueError, TypeError) as e:
        log.error(f"Error converting security config: {e}. Reverting defaults.")
        config = { k: defaults[k] for k in defaults }; config['password_min_length'] = max(4, int(defaults['password_min_length'])); config['session_timeout'] = max(5, int(defaults['session_timeout']))
        for k in ['password_require_special', 'password_require_numbers', 'password_require_uppercase']: config[k] = defaults[k].lower() == 'true'
    return config

def validate_password(password, security_config=None):
    if not password: return False, "Contraseña vacía."
    if security_config is None: security_config = get_security_config_values()
    min_length = security_config['password_min_length']; req_spec = security_config['password_require_special']; req_num = security_config['password_require_numbers']; req_upper = security_config['password_require_uppercase']
    if len(password) < min_length: return False, f"Mín {min_length} chars."
    if req_spec and not re.search(r"\W", password): return False, "Requiere especial."
    if req_num and not any(c.isdigit() for c in password): return False, "Requiere número."
    if req_upper and not any(c.isupper() for c in password): return False, "Requiere mayúscula."
    return True, "Válida."

# --- Gestión de Estado de Sesión (Sin cambios) ---
def init_session_state():
    now_with_tz = datetime.now(colombia_tz)
    defaults = { 'authenticated': False, 'username': None, 'user_id': None, 'role_name': None, 'permissions': set(), 'last_activity_time': now_with_tz, 'user_action': None, 'editing_user_id': None, 'deleting_user_id': None, 'role_action': None, 'editing_role_name': None, 'deleting_role_name': None, 'agent_action': None, 'editing_agent_id': None, 'deleting_agent_id': None, 'selected_agent_id': None, 'selected_agent_name': None, 'chat_messages': [], 'current_chat_agent_id': None, 'chat_session_id': None, 'chat_selected_agent_chat_url': None, 'selected_agent_id_for_crud': None, 'selected_role_id_for_crud': None }
    for key, default_value in defaults.items():
        if key not in st.session_state: st.session_state[key] = default_value
        elif key == 'last_activity_time':
            current_time_val = st.session_state.get(key)
            if not isinstance(current_time_val, datetime) or current_time_val.tzinfo is None: st.session_state[key] = now_with_tz

def update_last_activity(): st.session_state['last_activity_time'] = datetime.now(colombia_tz)

def check_session_timeout():
    if not st.session_state.get('authenticated', False): return False
    try:
        timeout_minutes = get_security_config_values()['session_timeout']; last_activity = st.session_state.get('last_activity_time')
        if not isinstance(last_activity, datetime): update_last_activity(); return False
        if last_activity.tzinfo is None:
            try: last_activity = colombia_tz.localize(last_activity); st.session_state['last_activity_time'] = last_activity
            except: update_last_activity(); return False
        if datetime.now(colombia_tz) - last_activity > timedelta(minutes=timeout_minutes):
            log.info(f"Session timeout user '{st.session_state.get('username')}'"); logout(silent=True); return True
    except Exception as e: log.error(f"Error check session timeout: {e}")
    return False

def check_authentication():
    if st.session_state.get('authenticated', False):
        if check_session_timeout(): return False # logout() ya hizo rerun
        else: update_last_activity(); return True
    return False

# --- Autenticación y Login (Sin cambios en authenticate_user) ---
def authenticate_user(username, password) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    hashed_password = hash_password(password)
    try:
        with get_db_session() as db:
            user = db.query(User).options(joinedload(User.role)).filter(User.username == username).first()
            if not user: return False, None, "Usuario o contraseña incorrectos."
            if user.password != hashed_password: return False, None, "Usuario o contraseña incorrectos."
            if user.status != 'active': return False, None, f"Cuenta inactiva."
            user.last_access = datetime.now(colombia_tz)
            perms = set(); role_name = "N/A"
            if user.role: role_name = user.role.name; perms = set(p.strip() for p in (user.role.permissions or '').split(',') if p.strip())
            user_info = {"user_id": user.id, "username": user.username, "email": user.email, "role_name": role_name, "permissions": perms }
            log.info(f"User '{username}' authenticated."); return True, user_info, None
    except Exception as e: log.error(f"DB error auth user {username}: {e}", exc_info=True); return False, None, "Error interno del servidor."

# --- Función de Login Page (MODIFICADA para usar st.switch_page) ---
def show_login_page():
    st.markdown(get_login_page_style(), unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        logo_url = get_configuration('logo_url', 'general', '')
        if logo_url: st.markdown(f'<div style="text-align:center;"><img src="{logo_url}" style="max-width:350px;height:auto;margin-bottom:1rem;"></div>', unsafe_allow_html=True)
        st.markdown("<h2 class='login-header-title'>IA-AMCO Dashboard</h2>", unsafe_allow_html=True)
        st.markdown("<p class='login-header-subtitle'>Administración de agentes IA</p>", unsafe_allow_html=True)
        st.markdown('<div style="height:1.5rem;"></div>', unsafe_allow_html=True)
        with st.container(): # Caja login
            st.markdown("<h3 class='login-box-title'>Acceso</h3>", unsafe_allow_html=True)
            st.markdown("<p class='login-box-subtitle'>Ingrese sus credenciales</p>", unsafe_allow_html=True)
            with st.form("login_form"):
                username = st.text_input("Usuario", key="login_username", placeholder="Usuario", label_visibility="collapsed")
                password = st.text_input("Contraseña", type="password", key="login_password", placeholder="Contraseña", label_visibility="collapsed")
                st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)
                submitted = st.form_submit_button("Iniciar Sesión", use_container_width=True)
                if submitted:
                    if not username or not password: st.error("Ingrese usuario y contraseña.")
                    else:
                        with st.spinner("Autenticando..."):
                            authenticated, user_info, error_msg = authenticate_user(username, password)
                        if authenticated:
                            st.session_state['authenticated'] = True
                            st.session_state['username'] = user_info['username']
                            st.session_state['user_id'] = user_info['user_id']
                            st.session_state['role_name'] = user_info['role_name']
                            st.session_state['permissions'] = user_info['permissions']
                            st.session_state['last_activity_time'] = datetime.now(colombia_tz)
                            for key in ['user_action','role_action','agent_action']: st.session_state.pop(key, None) # Limpiar
                            st.success("Inicio de sesión exitoso...")
                            time.sleep(0.5)
                            # --- CAMBIO AQUÍ: Usar switch_page ---
                            try:
                                # >>> ESTA LÍNEA YA ES CORRECTA EN TU CÓDIGO <<<
                                st.switch_page("pages/01_Vista_General.py")
                            except Exception as e_switch:
                                log.error(f"Failed to switch page after login: {e_switch}")
                                st.rerun() # Fallback# ...                          
                            # --- FIN CAMBIO ---
                        else: st.error(error_msg or "Usuario o contraseña incorrectos.")

# --- Logout (Sin cambios) ---
def logout(silent=False, message="Sesión cerrada."):
    log.info(f"Logging out user '{st.session_state.get('username', 'N/A')}'...")
    keys_to_clear = list(st.session_state.keys());
    for key in keys_to_clear:
        try: del st.session_state[key]
        except KeyError: pass
    st.session_state.update({'authenticated':False,'username':None,'user_id':None,'role_name':None,'permissions':set()})
    if not silent: st.success(message)
    time.sleep(0.5); st.rerun()

# --- Decoradores (Sin cambios) ---
def requires_permission(permission_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not check_authentication(): st.stop()
            if permission_name not in st.session_state.get('permissions', set()):
                 st.title("🚫 Acceso Denegado"); st.warning(f"Permiso: '{permission_name}' requerido."); st.stop()
            try: return func(*args, **kwargs)
            except Exception as e: log.error(f"Error in @requires_permission({permission_name}) for {func.__name__}: {e}", exc_info=True); st.error("Error inesperado."); st.stop()
        return wrapper
    return decorator

def requires_role(allowed_roles):
     if isinstance(allowed_roles, str): allowed_roles = [allowed_roles]
     allowed_roles_lower = set(role.lower() for role in allowed_roles)
     def decorator(func):
         def wrapper(*args, **kwargs):
             if not check_authentication(): st.stop()
             current_role = (st.session_state.get('role_name') or '').lower()
             if current_role not in allowed_roles_lower:
                  st.title("🚫 Acceso Restringido"); st.warning(f"Rol requerido: {', '.join(allowed_roles)}."); st.stop()
             try: return func(*args, **kwargs)
             except Exception as e: log.error(f"Error in @requires_role({allowed_roles}) for {func.__name__}: {e}", exc_info=True); st.error("Error inesperado."); st.stop()
         return wrapper
     return decorator
