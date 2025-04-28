# --- pages/08_Gestion_Usuarios.py (CORREGIDO - DetachedInstanceError y SyntaxError) ---

import streamlit as st
import pandas as pd
import re
from datetime import datetime
import pytz
import time
from sqlalchemy.exc import IntegrityError, OperationalError
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import joinedload # Asegurar importación

# Importaciones locales
from database.database import get_db_session
from database.models import User, Role
from auth.auth import requires_permission, hash_password, validate_password, get_security_config_values
from utils.helpers import is_valid_email
from utils.config import get_configuration
import logging
from utils.helpers import render_sidebar # <-- AÑADIR ESTA LÍNEA
from utils.styles import apply_global_styles

# --- LLAMAR A RENDER_SIDEBAR TEMPRANO ---
render_sidebar()
# --- FIN LLAMADA ---

log = logging.getLogger(__name__)

PAGE_PERMISSION = "Gestión de Usuarios"
try: colombia_tz = pytz.timezone(get_configuration('timezone', 'general', 'America/Bogota'))
except: colombia_tz = pytz.timezone('America/Bogota')

# --- Funciones Auxiliares ---
def load_user_data() -> Tuple[List[Dict[str, Any]], List[Tuple[str, int]], Optional[Exception], Optional[str]]:
    """Carga datos usuarios para tabla y selectbox. Devuelve (datos_tabla, opciones_select, error_obj, error_msg)."""
    users_data: List[Dict[str, Any]] = []; user_options: List[Tuple[str, int]] = []
    error: Optional[Exception] = None; error_message: Optional[str] = None
    log.info("[Gestión Usuarios] Loading users...")
    try:
        with get_db_session() as db:
            users_objects = db.query(User).options(joinedload(User.role)).order_by(User.username).all() # Query ya corregida
            log.info(f"[Gestión Usuarios] Found {len(users_objects)} users.")
            for user in users_objects:
                created=user.created_at.astimezone(colombia_tz).strftime('%Y-%m-%d %H:%M') if user.created_at else 'N/A'
                last=user.last_access.astimezone(colombia_tz).strftime('%Y-%m-%d %H:%M') if user.last_access else 'N/A'
                icon="🟢" if user.status == "active" else "🔴"
                role_name = user.role.name if user.role else "N/A"
                users_data.append({ "ID": user.id, "Usuario": user.username, "Email": user.email or "N/A", "Rol": role_name, "Estado": f"{icon} {user.status.capitalize()}", "Creado": created, "Último Acceso": last, })
                user_options.append((f"{user.username} (ID: {user.id})", user.id))
    except OperationalError as oe: log.error(f"[GU] OpError: {oe}",exc_info=True); error=oe; error_message=f"Error DB: {oe}"
    except Exception as e: log.error(f"[GU] Generic error: {e}",exc_info=True); error=e; error_message=f"Error: {e}"
    log.info(f"[GU] Load finished. Rows: {len(users_data)}, Error: {error is not None}")
    return users_data, user_options, error, error_message

# --- Funciones Dialog ---
@st.dialog("Crear Nuevo Usuario", width="large")
def create_user_dialog(): log.info("Render create user..."); render_user_form_content(mode='create')

@st.dialog("Editar Usuario", width="large")
def edit_user_dialog(user_id: int):
    log.info(f"Render edit user ID: {user_id}"); user_data={}; name=f"(ID: {user_id})"
    try:
        with get_db_session() as db:
            user = db.query(User).options(joinedload(User.role)).filter(User.id==user_id).first()
            if not user: st.error(f"ID {user_id} no."); time.sleep(1); st.session_state.user_action=None; st.session_state.editing_user_id=None; st.rerun(); return
            name=user.username; user_data={k: getattr(user, k) for k in User.__table__.columns.keys()}; user_data['current_role_id']=user.role_id if user.role else None; log.info(f"User data loaded edit {user_id}")
        st.subheader(f"Editando: {name} (ID: {user_id})")
        render_user_form_content(mode='edit', user_data=user_data, user_id_to_edit=user_id)
    except Exception as e:
         st.error(f"Error cargando user: {e}"); log.error(f"Fail load user {user_id}", exc_info=True)
         if st.button("Cerrar"): st.session_state.user_action=None; st.session_state.editing_user_id=None; st.rerun()

@st.dialog("Confirmar Eliminación")
def delete_user_dialog(user_id: int):
     log.info(f"Render delete dialog ID: {user_id}")
     try:
        with get_db_session() as db:
             user = db.query(User).filter(User.id==user_id).first()
             if not user: st.error(f"User ID {user_id} no."); time.sleep(1); st.session_state.user_action=None; st.session_state.deleting_user_id=None; st.rerun(); return
             is_super=(user.username or '').lower()=='superadmin'; is_self=(user.id==st.session_state.get('user_id'))
             if is_super or is_self: st.error(f"Usuario '{user.username}' no eliminable."); st.button("Cerrar", on_click=lambda:(st.session_state.update({'user_action':None,'deleting_user_id':None}), st.rerun())); return
             st.warning(f"❓ Eliminar '{user.username}' (ID: {user_id})?"); st.markdown("**Irreversible.**")
             c1,c2=st.columns(2)
             with c1:
                  if st.button("🗑️ Sí", type="primary", key="confirm_del_user"):
                       log.warning(f"Attempt delete {user_id}")
                       try:
                           # Borrar dentro de la misma sesión donde se cargó
                           db.delete(user); db.commit(); st.success(f"✅ '{user.username}' eliminado.")
                           st.session_state.user_action=None; st.session_state.deleting_user_id=None; time.sleep(1); st.rerun()
                       except Exception as del_e: st.error(f"❌ Error eliminando: {del_e}"); log.error(f"Error deleting user {user_id}", exc_info=True)
             with c2:
                  if st.button("❌ Cancelar", key="cancel_del_user"): st.session_state.user_action=None; st.session_state.deleting_user_id=None; st.rerun()
     except Exception as e:
         st.error(f"❌ Error preparando: {e}"); log.error(f"Error render delete {user_id}", exc_info=True)
         if st.button("Cerrar"): st.session_state.user_action=None; st.session_state.deleting_user_id=None; st.rerun()

# --- Contenido del Formulario (CORREGIDO SyntaxError y DetachedInstanceError) ---
def render_user_form_content(mode: str, user_data: Optional[Dict[str, Any]] = None, user_id_to_edit: Optional[int] = None):
    is_edit = mode == 'edit'; submit_label = "💾 Guardar" if is_edit else "✅ Crear"
    sec_conf=get_security_config_values(); pw_hint=f"Min {sec_conf['password_min_length']}c."
    # --- CORRECCIÓN SyntaxError: Separar Ifs ---
    if sec_conf['password_require_uppercase']: pw_hint += " M."
    if sec_conf['password_require_numbers']: pw_hint += " N."
    if sec_conf['password_require_special']: pw_hint += " E."
    # --- FIN CORRECCIÓN ---

    avail_roles={}; role_keys=[]; cur_role_idx=0; cur_user_role=(st.session_state.get('role_name') or '').lower()
    try: # --- CORRECCIÓN DetachedInstanceError: Procesar roles DENTRO de la sesión ---
        with get_db_session() as db:
            roles_db = db.query(Role).order_by(Role.name).all()
            log.info(f"[User Form] Loaded {len(roles_db)} roles from DB.")
            # Procesar roles aquí para obtener nombres y IDs
            is_editing_super = is_edit and (user_data.get('username') or '').lower()=='superadmin'
            current_role_id_in_edit = user_data.get('current_role_id') if is_edit else None
            temp_role_keys = [] # Lista temporal para mantener orden
            for r in roles_db:
                is_super_role = (r.name or '').lower()=='superadministrador'
                # Filtrar rol superadmin si el usuario actual no es superadmin
                if is_super_role and cur_user_role!='superadministrador': continue
                avail_roles[r.name] = r.id # Mapa nombre -> id
                temp_role_keys.append(r.name) # Añadir a lista ordenada
                # Encontrar índice para preselección en modo edición
                if is_edit and r.id == current_role_id_in_edit:
                     # El índice se calcula sobre temp_role_keys después del loop
                     pass # Solo necesitamos saber que existe
            role_keys = temp_role_keys # Asignar lista ordenada final
            # Calcular índice después de construir role_keys completo
            if is_edit and current_role_id_in_edit is not None:
                role_name_in_edit = next((name for name, id_ in avail_roles.items() if id_ == current_role_id_in_edit), None)
                if role_name_in_edit and role_name_in_edit in role_keys:
                    cur_role_idx = role_keys.index(role_name_in_edit)
                else:
                    # Si el rol actual del usuario no está en la lista disponible (ej. era superadmin y edita otro admin)
                    cur_role_idx = 0 # O seleccionar placeholder
                    if role_keys: # Añadir opción deshabilitada si no está disponible
                         log.warning(f"Current role ID {current_role_id_in_edit} not found in available roles for selection.")
                         # No podemos añadirla directamente al selectbox fácilmente si está deshabilitado

        # --- FIN CORRECCIÓN DetachedInstanceError ---
        if not avail_roles: st.error("No hay roles disponibles para asignar."); return # Salir si no hay roles

    except OperationalError as oe_roles: log.error(f"OpError loading roles: {oe_roles}"); st.error(f"Error DB: Tabla 'roles' no encontrada? ({oe_roles})"); return
    except Exception as e: st.error(f"Error cargando roles: {e}"); log.error("Error loading roles", exc_info=True); return

    # Renderizar Formulario (usa variables procesadas arriba)
    with st.form(key=f"{mode}_user_form"):
        st.markdown("* Obligatorio."); username_val=user_data.get('username','') if is_edit else ''; email_val=user_data.get('email','') if is_edit else ''; status_val=user_data.get('status','active') if is_edit else 'active'; status_idx=0 if status_val=='active' else 1
        username = st.text_input("Usuario *", value=username_val, disabled=is_edit); c1,c2=st.columns(2)
        with c1: email=st.text_input("Email *", value=email_val, key="f_email"); role_dis=is_editing_super; sel_role=st.selectbox("Rol *", options=role_keys, index=cur_role_idx, key="f_role", disabled=role_dis); st.caption("Rol Superadmin no modificable.") if role_dis else None
        with c2: stat_dis=is_editing_super or (is_edit and user_id_to_edit==st.session_state.get('user_id')); status=st.selectbox("Estado *",["active","inactive"], index=status_idx, key="f_status", disabled=stat_dis); st.caption("No inactivar Superadmin/usted.") if stat_dis else None
        st.markdown("---"); st.subheader("Contraseña")
        pwd_chg_dis=is_editing_super and cur_user_role!='superadministrador'; new_pwd, conf_pwd = None, None
        if is_edit: chg_pwd=st.checkbox("Cambiar", key="f_chg_pwd", disabled=pwd_chg_dis); st.caption("Dejar en blanco para no cambiar.")
        else: chg_pwd=True
        if chg_pwd and not pwd_chg_dis: new_pwd=st.text_input("Nueva *" if not is_edit else "Nueva", type="password", key="f_pwd1", help=pw_hint); conf_pwd=st.text_input("Confirmar *" if not is_edit else "Confirmar", type="password", key="f_pwd2")
        elif pwd_chg_dis: st.caption("Contraseña Superadmin no modificable.")
        st.markdown("---"); submitted=st.form_submit_button(submit_label, type="primary")

        if submitted: # Lógica de validación y guardado (sin cambios)
            errs=[]; new_role_id=avail_roles.get(sel_role)
            if not is_edit and not username.strip(): errs.append("Usuario.")
            if not email.strip() or not is_valid_email(email.strip()): errs.append("Email válido.")
            if not new_role_id: errs.append("Rol.")
            pwd_save=user_data.get('password') if is_edit else None; valid_new_pwd = False
            if chg_pwd and not pwd_chg_dis:
                 if not new_pwd or not conf_pwd: errs.append("Complete pwd.")
                 elif new_pwd!=conf_pwd: errs.append("Pwd no coinciden.")
                 else: valid_new_pwd,msg=validate_password(new_pwd,sec_conf); errs.append(msg) if not valid_new_pwd else (pwd_save:=hash_password(new_pwd))
            elif not is_edit and pwd_save is None : errs.append("Contraseña obligatoria.")
            if not errs: # Check unicidad
                with get_db_session() as db:
                    uname=username.strip(); mail=email.strip()
                    if not is_edit and db.query(User).filter(User.username==uname).count()>0: errs.append(f"User '{uname}' ya existe.")
                    if (not is_edit or mail!=user_data.get('email')) and db.query(User).filter(User.email==mail, User.id!=user_id_to_edit).count()>0: errs.append(f"Email '{mail}' ya registrado.")
            if errs:
                for e in errs: st.error(f"⚠️ {e}")
            else: # Guardar
                try:
                    with get_db_session() as db:
                        if is_edit:
                            user_upd=db.query(User).filter(User.id==user_id_to_edit).first()
                            if not user_upd: raise ValueError("Usuario no.")
                            user_upd.email=email.strip();
                            if not role_dis: user_upd.role_id=new_role_id
                            if not stat_dis: user_upd.status=status
                            if chg_pwd and not pwd_chg_dis and valid_new_pwd: user_upd.password=pwd_save # <-- Corregido: usar chg_pwd flag
                            st.success(f"✅ '{user_upd.username}' actualizado.")
                        else:
                            new_user=User(username=username.strip(), email=email.strip(), password=pwd_save, role_id=new_role_id, status=status, created_at=datetime.now(colombia_tz))
                            db.add(new_user); st.success(f"✅ '{username.strip()}' creado.")
                    st.session_state.user_action=None; st.session_state.editing_user_id=None; time.sleep(1); st.rerun()
                except IntegrityError: st.error(f"⚠️ Error: Usuario o Email ya existen.")
                except Exception as e: st.error(f"❌ Error guardando: {e}"); log.error("Error saving user", exc_info=True)
    if st.button("Cancelar", key=f"cancel_{mode}_user_btn"): st.session_state.user_action=None; st.session_state.editing_user_id=None; st.rerun()

# --- Página Principal ---
@requires_permission(PAGE_PERMISSION)
def show_user_management_page():
    st.title("👤 Gestión Usuarios"); st.caption("Crear, visualizar, editar, eliminar.")
    try:
        # Llamar función de carga
        users_data, user_options, error_load, error_message = load_user_data() # Usa nueva función
        if st.button("🔄 Refrescar"): st.rerun()
        if error_load: st.error(error_message or "Error."); st.stop()
        if users_data: st.dataframe(pd.DataFrame(users_data), use_container_width=True, hide_index=True, column_config={"ID":st.column_config.NumberColumn(width="small"), "Estado":st.column_config.TextColumn(width="small"), "Creado":st.column_config.DatetimeColumn(format="YYYY-MM-DD HH:mm"), "Último Acceso":st.column_config.DatetimeColumn(format="YYYY-MM-DD HH:mm"),})
        else: st.info("No hay usuarios.")
        st.divider(); st.subheader("Acciones"); c1,c2,c3=st.columns([1.5,3,1.5])
        with c1:
            if st.button("➕ Crear", use_container_width=True): st.session_state.user_action='create'; st.session_state.editing_user_id=None; st.session_state.deleting_user_id=None
        with c2:
            # Usar user_options (lista de tuples) para crear mapa
            opts_map={l:i for l,i in user_options}; opts_disp={"":"Seleccione..."}; opts_disp.update(opts_map)
            sel_lbl=st.selectbox("Sel:", options=list(opts_disp.keys()), index=0, label_visibility="collapsed", key="user_select_crud")
            st.session_state.selected_user_id_for_crud = opts_disp.get(sel_lbl)
        with c3:
             ce,cd=st.columns(2); cur_sel=st.session_state.get("selected_user_id_for_crud"); cur_user_id=st.session_state.get('user_id')
             can_del=False; del_tooltip="Eliminar"
             sel_user_name = None
             if cur_sel: sel_user_name=next((u['Usuario'] for u in users_data if u['ID']==cur_sel),None) # Buscar nombre en datos de tabla
             if sel_user_name and (sel_user_name or '').lower()!='superadmin' and cur_sel!=cur_user_id: can_del=True
             elif sel_user_name: del_tooltip="No eliminable"
             with ce:
                  if st.button("✏️", key="edit_btn", help="Editar", use_container_width=True, disabled=not cur_sel): st.session_state.user_action='edit'; st.session_state.editing_user_id=cur_sel; st.session_state.deleting_user_id=None
             with cd:
                  if st.button("🗑️", key="del_btn", help=del_tooltip, use_container_width=True, disabled=not can_del): st.session_state.user_action='delete'; st.session_state.deleting_user_id=cur_sel; st.session_state.editing_user_id=None
        action=st.session_state.get('user_action'); edit_id=st.session_state.get('editing_user_id'); del_id=st.session_state.get('deleting_user_id')
        log.debug(f"Dialog check GU: act={action}, ed={edit_id}, del={del_id}")
        if action=='create': create_user_dialog()
        elif action=='edit' and edit_id is not None: edit_user_dialog(user_id=edit_id)
        elif action=='delete' and del_id is not None: delete_user_dialog(user_id=del_id)
    except Exception as page_e: log.error(f"Error page Users: {page_e}", exc_info=True); st.error(f"Error: {page_e}")

apply_global_styles()
show_user_management_page()
