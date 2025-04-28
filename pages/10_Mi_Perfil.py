# --- pages/10_Mi_Perfil.py (CORREGIDO - SyntaxError y st.select) ---

import streamlit as st
import time
from sqlalchemy.orm import joinedload # <--- IMPORTADO joinedload

# Importaciones locales
from auth.auth import hash_password, validate_password, get_security_config_values
from database.database import get_db_session
from database.models import User, Role
from utils.helpers import is_valid_email
import logging
from utils.helpers import render_sidebar # <-- AÑADIR ESTA LÍNEA
from utils.styles import apply_global_styles

# --- LLAMAR A RENDER_SIDEBAR TEMPRANO ---
render_sidebar()
# --- FIN LLAMADA ---

log = logging.getLogger(__name__)

def show_profile_page():
    st.title("👤 Mi Perfil"); st.caption("Actualiza tu información personal y contraseña.")
    user_id = st.session_state.get('user_id')
    if not user_id: st.error("Error: Sesión no identificada."); st.stop()

    try:
        with get_db_session() as db:
            # --- CORRECCIÓN QUERY ---
            user = db.query(User).options(
                joinedload(User.role) # Usar joinedload correctamente
            ).filter(User.id == user_id).first()
            # --- FIN CORRECCIÓN ---
            if not user: st.error("Error: Usuario no encontrado."); st.session_state['authenticated']=False; time.sleep(1); st.rerun(); st.stop()

            sec_conf=get_security_config_values(); pw_hint=f"Min {sec_conf['password_min_length']}c."
            # --- CORRECCIÓN SyntaxError: Separar Ifs ---
            if sec_conf['password_require_uppercase']: pw_hint += " M."
            if sec_conf['password_require_numbers']: pw_hint += " N."
            if sec_conf['password_require_special']: pw_hint += " E."
            # --- FIN CORRECCIÓN ---

            with st.form("profile_form"):
                st.subheader("Información"); c1, c2 = st.columns(2)
                with c1: st.text_input("Usuario", value=user.username, disabled=True)
                with c2: st.text_input("Rol", value=user.role.name if user.role else "N/A", disabled=True)
                email = st.text_input("Email *", value=user.email or "", key="profile_email")
                st.markdown("---"); st.subheader("Cambiar Contraseña (Opcional)")
                chg_pwd = st.checkbox("Cambiar", key="profile_chg_pwd")
                pwd_curr, pwd_new1, pwd_new2 = None, None, None
                if chg_pwd:
                    pwd_curr=st.text_input("Actual *", type="password", key="profile_curr_pwd")
                    c_pwd1, c_pwd2 = st.columns(2)
                    with c_pwd1: pwd_new1=st.text_input("Nueva *", type="password", key="profile_new_pwd1", help=pw_hint)
                    with c_pwd2: pwd_new2=st.text_input("Confirmar Nueva *", type="password", key="profile_new_pwd2")
                st.markdown("---"); submitted = st.form_submit_button("💾 Guardar Cambios", type="primary", use_container_width=True)

                if submitted:
                    errors = []; email_changed = (st.session_state.profile_email != user.email); pwd_req = chg_pwd; valid_new_pwd = False
                    # Validar Email
                    if email_changed:
                        new_email = st.session_state.profile_email
                        if not is_valid_email(new_email): errors.append("Email inválido.")
                        else:
                             with get_db_session() as db_check:
                                 if db_check.query(User).filter(User.email==new_email, User.id!=user_id).first(): errors.append(f"Email '{new_email}' ya en uso.")
                    # Validar Contraseña
                    if pwd_req:
                        if not pwd_curr or not pwd_new1 or not pwd_new2: errors.append("Complete campos contraseña.")
                        elif hash_password(pwd_curr) != user.password: errors.append("Contraseña actual incorrecta.")
                        elif pwd_new1 != pwd_new2: errors.append("Nuevas contraseñas no coinciden.")
                        else: valid_new_pwd, pwd_msg = validate_password(pwd_new1, sec_conf); errors.append(pwd_msg) if not valid_new_pwd else None
                    # Guardar
                    if errors:
                        for e in errors: st.error(f"⚠️ {e}")
                    else:
                        changed = False
                        try:
                            with get_db_session() as db_save:
                                user_upd = db_save.query(User).filter(User.id == user_id).first()
                                if not user_upd: raise ValueError("Usuario no encontrado.")
                                if email_changed: user_upd.email = st.session_state.profile_email; changed = True; log.info(f"User '{user.username}' updated email.")
                                if pwd_req and valid_new_pwd: user_upd.password = hash_password(pwd_new1); changed = True; log.info(f"User '{user.username}' updated password.")
                                if changed: db_save.commit(); st.success("✅ ¡Perfil actualizado!")
                                else: st.info("ℹ️ No se detectaron cambios.")
                                for k in ['profile_curr_pwd','profile_new_pwd1','profile_new_pwd2']: st.session_state.pop(k, None)
                        except Exception as e: st.error(f"❌ Error guardando perfil: {e}"); log.error("Error saving profile", exc_info=True)
    except Exception as e: st.error(f"Error cargando datos perfil: {e}"); log.error("Error loading profile page", exc_info=True)

apply_global_styles()
show_profile_page()
