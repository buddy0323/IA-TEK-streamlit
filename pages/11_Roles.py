# --- pages/11_Roles.py (CORREGIDO - Query Columnas + Safe Lower + Dialog Load) ---

import streamlit as st
import pandas as pd
import time
from sqlalchemy.exc import IntegrityError, OperationalError
from typing import Optional, List, Tuple, Dict, Any, Set

# Importar dependencias locales
from auth.auth import requires_permission
from database.database import get_db_session
from database.models import Role, User
import logging
from utils.helpers import render_sidebar # <-- AÑADIR ESTA LÍNEA

# --- LLAMAR A RENDER_SIDEBAR TEMPRANO ---
render_sidebar()
# --- FIN LLAMADA ---

log = logging.getLogger(__name__)

PAGE_PERMISSION = "Roles"
ALL_PERMISSIONS = sorted([
    "Vista General", "Gestión de agentes IA", "Agentes IA", "Entrenar", "Monitoreo",
    "Historial de Conversaciones", "Análisis de Consultas", "Gestión de Usuarios",
    "Configuración", "Mi Perfil", "Roles"])

# --- Funciones Auxiliares ---
# MODIFICADA: Carga datos específicos, no objetos Role completos para la lista principal
def load_roles_data_for_display() -> Tuple[List[Dict[str, Any]], List[Tuple[str, int]], Optional[Exception], Optional[str]]:
    """Carga datos de roles para tabla y selectbox. Devuelve (datos_tabla, opciones_select, error_obj, error_msg)."""
    roles_data_for_table: List[Dict[str, Any]] = []
    role_options_for_select: List[Tuple[str, int]] = [] # (Label, ID)
    error: Optional[Exception] = None; error_message: Optional[str] = None
    log.info("[Roles] Loading roles from DB...")
    try:
        with get_db_session() as db:
            log.info("[Roles] DB session obtained.")
            # Query para seleccionar solo columnas necesarias para display/select
            roles_result = db.query(
                Role.id, Role.name, Role.description, Role.permissions
            ).order_by(Role.name).all()
            log.info(f"[Roles] Query OK. Found {len(roles_result)} roles.")

            # Procesar resultados (ahora son tuples)
            for role_id, role_name, role_desc, role_perms in roles_result:
                permissions_set = set(p.strip() for p in (role_perms or '').split(',') if p.strip())
                roles_data_for_table.append({
                    "ID": role_id, "Nombre": role_name, "Descripción": role_desc or "",
                    "Permisos": ", ".join(sorted(permissions_set))
                })
                # Asegurar que role_name no sea None antes de formatear el label
                safe_role_name = role_name or "Nombre Inválido"
                role_options_for_select.append((f"{safe_role_name} (ID: {role_id})", role_id)) # (Label, ID)

    except OperationalError as oe: log.error(f"[Roles] OpError: {oe}", exc_info=True); error=oe; error_message=f"Error DB: {oe}"
    except Exception as e: log.error(f"[Roles] Generic error: {e}", exc_info=True); error=e; error_message=f"Error: {e}"
    log.info(f"[Roles] Load finished. Rows: {len(roles_data_for_table)}, Error: {error is not None}")
    return roles_data_for_table, role_options_for_select, error, error_message

# --- Funciones Dialog ---
@st.dialog("Crear Nuevo Rol", width="large")
def create_role_dialog():
    log.info("Render create role...");
    # Pasar permisos globales y si el usuario es superadmin
    is_super = (st.session_state.get('role_name') or '').lower() == 'superadministrador'
    render_role_form_content(mode='create', current_permissions=None, all_permissions=ALL_PERMISSIONS, is_superadmin_calling=is_super)

@st.dialog("Editar Rol", width="large")
def edit_role_dialog(role_id: int):
    log.info(f"Render edit role ID: {role_id}"); role_name = f"(ID: {role_id})"
    try:
        with get_db_session() as db: # Cargar objeto COMPLETO aquí dentro
            role_instance = db.query(Role).filter(Role.id == role_id).first()
            if not role_instance: st.error(f"Rol ID {role_id} no."); time.sleep(1); st.session_state.role_action=None; st.session_state.editing_role_id=None; st.rerun(); return
            role_name = role_instance.name
            # Extraer datos necesarios MIENTRAS está en sesión
            current_description = role_instance.description
            current_permissions_set = role_instance.get_permissions_set()
            log.info(f"Role data loaded edit ID {role_id}")

        st.subheader(f"Editando: {role_name} (ID: {role_id})")
        # Pasar datos primitivos y el ID
        is_super = (st.session_state.get('role_name') or '').lower() == 'superadministrador'
        render_role_form_content(mode='edit', role_name=role_name, current_description=current_description, current_permissions=current_permissions_set, all_permissions=ALL_PERMISSIONS, is_superadmin_calling=is_super, role_id_to_edit=role_id)
    except Exception as e:
         st.error(f"Error cargando rol: {e}"); log.error(f"Fail load role {role_id}", exc_info=True)
         if st.button("Cerrar"): st.session_state.role_action=None; st.session_state.editing_role_id=None; st.rerun()

@st.dialog("Confirmar Eliminación de Rol")
def delete_role_dialog(role_id: int):
     log.info(f"Render delete dialog ID: {role_id}")
     try:
        with get_db_session() as db: # Cargar y verificar dentro de sesión
             role_to_delete = db.query(Role).filter(Role.id == role_id).first()
             if not role_to_delete: st.error(f"Rol ID {role_id} no."); time.sleep(1); st.session_state.role_action=None; st.session_state.deleting_role_id=None; st.rerun(); return
             role_name = role_to_delete.name
             if (role_name or '').lower() == 'superadministrador': st.error("Rol 'superadministrador' no eliminable."); st.button("Cerrar", on_click=lambda:(st.session_state.update({'role_action':None,'deleting_role_id':None}), st.rerun())); return
             user_count = db.query(User).filter(User.role_id == role_id).count()
             if user_count > 0: st.error(f"Rol '{role_name}' asignado a {user_count} usuario(s)."); st.button("Cerrar", on_click=lambda:(st.session_state.update({'role_action':None,'deleting_role_id':None}), st.rerun())); return
             # Mostrar confirmación
             st.warning(f"❓ Eliminar rol '{role_name}' (ID: {role_id})?"); st.markdown("**Irreversible.**")
             c1, c2 = st.columns(2)
             with c1:
                  if st.button("🗑️ Sí", type="primary", key="confirm_del_role"):
                       log.warning(f"Attempt delete {role_id}")
                       try: # Borrar DENTRO de la misma sesión
                           db.delete(role_to_delete); db.commit()
                           st.success(f"✅ Rol '{role_name}' eliminado."); log.info(f"Role {role_id} deleted.")
                           st.session_state.role_action=None; st.session_state.deleting_role_id=None; time.sleep(1); st.rerun()
                       except Exception as del_e: log.error(f"Error deleting {role_id}", exc_info=True); st.error(f"❌ Error: {del_e}")
             with c2:
                  if st.button("❌ Cancelar", key="cancel_del_role"): st.session_state.role_action=None; st.session_state.deleting_role_id=None; st.rerun()
     except Exception as e:
         st.error(f"❌ Error preparando: {e}"); log.error(f"Error render delete {role_id}", exc_info=True)
         if st.button("Cerrar"): st.session_state.role_action=None; st.session_state.deleting_role_id=None; st.rerun()


# --- Contenido del Formulario (Recibe datos primitivos) ---
def render_role_form_content(mode: str, all_permissions: List[str], is_superadmin_calling: bool, role_name: Optional[str] = None, current_description: Optional[str] = None, current_permissions: Optional[Set[str]] = None, role_id_to_edit: Optional[int] = None):
    is_edit = mode == 'edit'; submit_label = "💾 Guardar" if is_edit else "✅ Crear"
    is_super_role_being_edited = is_edit and (role_name or '').lower() == 'superadministrador'

    # Defaults
    d_name = role_name if is_edit else ''; d_desc = current_description or '' if is_edit else ''
    d_perms = current_permissions if is_edit else {"Vista General", "Mi Perfil"}

    with st.form(key=f"{mode}_role_form"):
        st.markdown("* Obligatorio."); name = st.text_input("Nombre Rol *", value=d_name, disabled=is_edit); description = st.text_area("Descripción", value=d_desc)
        st.markdown("---"); st.subheader("Permisos *"); sel_perms = set(); c1,c2,c3=st.columns(3); cols=[c1,c2,c3]; idx=0
        for perm in all_permissions:
            disabled = is_super_role_being_edited or (perm in ["Configuración", "Roles"] and not is_superadmin_calling)
            checked = perm in d_perms or is_super_role_being_edited
            with cols[idx % 3]:
                if st.checkbox(perm, value=checked, disabled=disabled, key=f"{mode}_perm_{perm}"): sel_perms.add(perm)
            idx += 1
        st.markdown("---"); submitted=st.form_submit_button(submit_label, type="primary")
        if submitted:
            errs=[]; final_name = name.strip() if not is_edit else role_name
            if not is_edit and not final_name: errs.append("Nombre.")
            elif not is_edit and final_name.lower()=='superadministrador': errs.append("Nombre reservado.")
            if not sel_perms: errs.append("Seleccione permisos.")
            if not errs and not is_edit:
                with get_db_session() as db:
                    if db.query(Role).filter(Role.name == final_name).count()>0: errs.append(f"Rol '{final_name}' ya existe.")
            if errs:
                for e in errs: st.error(f"⚠️ {e}"); return
            perms_str=",".join(sorted(list(sel_perms)))
            try: # Guardar
                with get_db_session() as db:
                    if is_edit:
                        log.info(f"Updating role ID: {role_id_to_edit}")
                        role_upd = db.query(Role).filter(Role.id == role_id_to_edit).first()
                        if not role_upd: raise ValueError("Rol no encontrado.")
                        role_upd.description = description.strip(); role_upd.permissions = perms_str
                        st.success(f"✅ Rol '{role_upd.name}' actualizado.")
                    else:
                        log.info(f"Creating role: {final_name}")
                        new_role = Role(name=final_name, description=description.strip(), permissions=perms_str)
                        db.add(new_role); st.success(f"✅ Rol '{final_name}' creado.")
                st.session_state.role_action=None; st.session_state.editing_role_id=None; st.session_state.deleting_role_id=None; time.sleep(1); st.rerun()
            except IntegrityError: st.error(f"⚠️ Error: Ya existe rol '{final_name}'.")
            except Exception as e: st.error(f"❌ Error guardando: {e}"); log.error("Error saving role", exc_info=True)
    if st.button("Cancelar", key=f"cancel_{mode}_role_btn"): st.session_state.role_action=None; st.session_state.editing_role_id=None; st.session_state.deleting_role_id=None; st.rerun()

# --- Página Principal ---
@requires_permission(PAGE_PERMISSION)
def show_roles_management_page():
    st.title("🎭 Roles y Permisos"); st.caption("Define roles y sus permisos.")
    try:
        # Usar la función modificada que no devuelve objetos Role
        roles_data, role_options, error_load, error_message = load_roles_data_for_display()
        if st.button("🔄 Refrescar"): st.rerun()
        if error_load: st.error(error_message or "Error."); st.warning("Verifica BD."); st.stop()
        if roles_data: st.dataframe(pd.DataFrame(roles_data), use_container_width=True, hide_index=True, column_config={"ID":st.column_config.NumberColumn(width="small"), "Nombre":st.column_config.TextColumn(width="medium"), "Descripción":st.column_config.TextColumn(width="large"), "Permisos":st.column_config.TextColumn(width="xlarge"),})
        else: st.info("No hay roles.")
        st.divider(); st.subheader("Acciones"); c1,c2,c3=st.columns([1.5,3,1.5])
        # --- CORRECCIÓN AttributeError: usar get con default y luego lower ---
        current_user_role_lower = (st.session_state.get('role_name') or '').lower()
        is_super = current_user_role_lower == 'superadministrador'
        # --- FIN CORRECCIÓN ---
        with c1:
            if st.button("➕ Crear", use_container_width=True, disabled=not is_super): st.session_state.role_action='create'; st.session_state.editing_role_id=None; st.session_state.deleting_role_id=None
        with c2:
            # Usar role_options (lista de tuples) para crear mapa
            opts_map={label: id_ for label, id_ in role_options}; opts_disp={"":"Seleccione..."}; opts_disp.update(opts_map)
            sel_lbl=st.selectbox("Sel:", options=list(opts_disp.keys()), index=0, label_visibility="collapsed", key="role_select_crud")
            st.session_state.selected_role_id_for_crud = opts_disp.get(sel_lbl) # Guardar ID
        with c3:
             ce,cd=st.columns(2); cur_sel_id=st.session_state.get("selected_role_id_for_crud"); cur_sel_name=None
             if cur_sel_id: cur_sel_name = next((lbl.split(' (')[0] for lbl,id_ in opts_map.items() if id_==cur_sel_id), None)
             # --- CORRECCIÓN AttributeError: usar get con default y luego lower ---
             cur_sel_name_lower = (cur_sel_name or '').lower()
             can_edit=is_super and cur_sel_id and cur_sel_name_lower != 'superadministrador'
             can_del=can_edit # Check de uso se hace en dialog
             del_tooltip="Eliminar" if can_del else "No eliminable";
             if not is_super and cur_sel_id: del_tooltip="Solo Superadmin"
             # --- FIN CORRECCIÓN ---
             with ce:
                  if st.button("✏️", key="edit_role_btn", help="Editar", use_container_width=True, disabled=not can_edit): st.session_state.role_action='edit'; st.session_state.editing_role_id=cur_sel_id; st.session_state.deleting_role_id=None
             with cd:
                  disable_del = not cur_sel_id or cur_sel_name_lower == 'superadministrador' or not is_super
                  if st.button("🗑️", key="del_role_btn", help=del_tooltip, use_container_width=True, disabled=disable_del): st.session_state.role_action='delete'; st.session_state.deleting_role_id=cur_sel_id; st.session_state.editing_role_id=None
        action=st.session_state.get('role_action'); edit_id=st.session_state.get('editing_role_id'); del_id=st.session_state.get('deleting_role_id')
        if action=='create': create_role_dialog()
        elif action=='edit' and edit_id is not None: edit_role_dialog(role_id=edit_id)
        elif action=='delete' and del_id is not None: delete_role_dialog(role_id=del_id)
    except Exception as page_e: log.error(f"Error page Roles: {page_e}", exc_info=True); st.error(f"Error: {page_e}")

show_roles_management_page()
