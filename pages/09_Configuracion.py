# --- pages/09_Configuracion.py (Corregido DetachedInstanceError en CRUD Opciones) ---

import streamlit as st
import time
import pytz
import pandas as pd
from sqlalchemy.exc import IntegrityError, OperationalError

# Importaciones locales
from auth.auth import requires_role
from utils.config import get_configuration, save_configuration
from utils.api_client import test_agentops_connection, test_anthropic_connection, test_openai_connection
from database.database import get_db_session
from database.models import LanguageModelOption, SkillOption, PersonalityOption, GoalOption, Configuration
import logging
from utils.helpers import render_sidebar # <-- AÑADIR ESTA LÍNEA
from utils.styles import apply_global_styles

# --- LLAMAR A RENDER_SIDEBAR TEMPRANO ---
render_sidebar()
# --- FIN LLAMADA ---

log = logging.getLogger(__name__)

# --- Funciones Auxiliares para CRUD de Opciones (CORREGIDO) ---
def crud_options_ui(option_model, model_name_singular: str, model_name_plural: str):
    """Genera UI para CRUD de opciones, procesando datos dentro de la sesión."""
    st.subheader(f"Gestionar {model_name_plural}")
    options_data = [] # Lista para almacenar datos procesados (dicts o tuples)
    options_exist = False # Flag para saber si hay opciones
    try:
        with get_db_session() as db:
            # Cargar objetos
            options_objects = db.query(option_model).order_by(option_model.name).all()
            # --- PROCESAR DATOS DENTRO DE LA SESIÓN ---
            options_data = [
                {"ID": opt.id, "Nombre": opt.name, "Descripción": opt.description or ''}
                for opt in options_objects
            ]
            options_exist = bool(options_data)
            log.info(f"Loaded {len(options_data)} options for {model_name_plural}")
            # --- FIN PROCESAMIENTO ---

        # Mostrar tabla FUERA de la sesión, usando los datos procesados
        if options_data:
            st.dataframe(pd.DataFrame(options_data), use_container_width=True, hide_index=True)
        else:
            st.info(f"No hay {model_name_plural.lower()} definidos.")

    except OperationalError as oe_opts:
         log.error(f"OpError options {model_name_plural}: {oe_opts}")
         st.error(f"Error: Tabla '{option_model.__tablename__}' no existe. Aplica migración '012'.")
         return # No mostrar el resto si tabla no existe
    except Exception as e:
        log.error(f"Error loading {model_name_plural}: {e}", exc_info=True)
        st.error(f"Error cargando {model_name_plural.lower()}: {e}")
        return

    st.markdown("---")
    # Añadir (Formulario igual que antes)
    with st.expander(f"➕ Añadir {model_name_singular}"):
        with st.form(key=f"add_{option_model.__tablename__}_form"):
            name = st.text_input("Nombre *"); desc = st.text_area("Descripción")
            if st.form_submit_button(f"Añadir"):
                if not name.strip(): st.error("Nombre obligatorio.")
                else:
                    try:
                        with get_db_session() as db: db.add(option_model(name=name.strip(), description=desc.strip())); db.commit()
                        st.success(f"'{name.strip()}' añadido."); time.sleep(0.5); st.rerun()
                    except IntegrityError: st.error(f"Error: Ya existe '{name.strip()}'.")
                    except Exception as e: st.error(f"Error añadiendo: {e}")

    # Eliminar (Usa options_data ahora para el selectbox)
    with st.expander(f"🗑️ Eliminar {model_name_singular}"):
        if options_exist: # Usar el flag
             # Crear diccionario para selectbox a partir de options_data
             opts = {f"{opt['Nombre']} (ID: {opt['ID']})": opt['ID'] for opt in options_data}
             lbl = st.selectbox(f"Seleccionar a eliminar", [""] + list(opts.keys()), index=0, key=f"del_{option_model.__tablename__}_sel")
             if lbl and st.button(f"Eliminar '{lbl.split(' (')[0]}'", type="secondary", key=f"del_{option_model.__tablename__}_btn"):
                  oid = opts[lbl]
                  try:
                      with get_db_session() as db: # Nueva sesión para borrar
                          o_db = db.query(option_model).filter(option_model.id == oid).first()
                          if o_db: db.delete(o_db); db.commit(); st.success(f"'{o_db.name}' eliminado."); time.sleep(0.5); st.rerun()
                          else: st.warning("Ya no existe.")
                  except Exception as e: st.error(f"Error eliminando: {e}. ¿En uso?")
        else: st.caption(f"Nada para eliminar.")

# --- Página Principal y otras secciones (sin cambios) ---
@requires_role("superadministrador")
def show_config_page():
    st.title("⚙️ Configuración"); st.caption("Gestiona APIs, opciones, apariencia y seguridad.")
    tabs = st.tabs(["🔌 APIs", "🧩 Opciones Agentes", "⚙️ General", "🎨 Apariencia", "🔒 Seguridad"])
    with tabs[0]: api_config_section()
    with tabs[1]: options_agents_tab_content()
    with tabs[2]: general_config_section()
    with tabs[3]: appearance_config_section()
    with tabs[4]: security_config_section()

def api_config_section(): # Sin cambios
    st.header("APIs"); st.caption("Credenciales.");
    with st.form("api_config_form"):
        st.subheader("N8N"); st.text_input("Usuario N8N", value=get_configuration('n8n_username', 'api', ''), key="cfg_form_n8n_user"); st.text_input("Contraseña N8N", type="password", value=get_configuration('n8n_password', 'api', ''), key="cfg_form_n8n_pass")
        st.markdown("---"); st.subheader("Otras"); t1, t2, t3 = st.tabs(["AgentOps", "Anthropic", "OpenAI"])
        with t1: st.text_input("AgentOps Key", type="password", value=get_configuration('agentops_api_key', 'api', ''), key="cfg_form_agentops_key")
        with t2: st.text_input("Anthropic Key", type="password", value=get_configuration('anthropic_api_key', 'api', ''), key="cfg_form_anthropic_key")
        with t3: st.text_input("OpenAI Key", type="password", value=get_configuration('openai_api_key', 'api', ''), key="cfg_form_openai_key")
        st.markdown("---"); submitted = st.form_submit_button("💾 Guardar APIs", type="primary")
        if submitted:
             kvs = {'n8n_username': st.session_state.cfg_form_n8n_user,'n8n_password': st.session_state.cfg_form_n8n_pass, 'agentops_api_key': st.session_state.cfg_form_agentops_key, 'anthropic_api_key': st.session_state.cfg_form_anthropic_key, 'openai_api_key': st.session_state.cfg_form_openai_key}; ok = True; errs = []
             try:
                 with get_db_session() as db:
                      for k, v in kvs.items():
                           if not save_configuration(k, v or '', 'api', db_session=db): ok = False; errs.append(f"'{k}'")
                 if ok: st.success("✅ APIs guardadas."); time.sleep(1)
                 else: st.warning(f"⚠️ Error APIs: {', '.join(errs)}")
             except Exception as e: st.error(f"Error fatal APIs: {e}")
    st.markdown("---"); st.subheader("Probar"); c1, c2, c3 = st.columns(3)
    with c1:
         if st.button("Probar AgentOps"): k = get_configuration('agentops_api_key', 'api'); test_agentops_connection(k) if k else st.warning("No key.")
    with c2:
         if st.button("Probar Anthropic"): k = get_configuration('anthropic_api_key', 'api'); test_anthropic_connection(k) if k else st.warning("No key.")
    with c3:
         if st.button("Probar OpenAI"): k = get_configuration('openai_api_key', 'api'); test_openai_connection(k) if k else st.warning("No key.")

def options_agents_tab_content(): # Sin cambios
    st.header("Opciones Agentes"); st.caption("Define opciones disponibles.")
    opt_tabs = st.tabs(["🤖 Modelos", "🛠️ Habilidades", "🎭 Personalidades", "🎯 Objetivos"])
    with opt_tabs[0]: crud_options_ui(LanguageModelOption, "Modelo", "Modelos")
    with opt_tabs[1]: crud_options_ui(SkillOption, "Habilidad", "Habilidades") # Usa nombre traducido
    with opt_tabs[2]: crud_options_ui(PersonalityOption, "Personalidad", "Personalidades")
    with opt_tabs[3]: crud_options_ui(GoalOption, "Objetivo", "Objetivos")

def general_config_section(): # Sin cambios
    st.header("General"); st.caption("Opciones generales.")
    with st.form("general_config_form"):
        name=get_configuration('dashboard_name','general','IA-AMCO'); tz=get_configuration('timezone','general','America/Bogota')
        st.text_input("Nombre Dashboard *", value=name, key="cfg_form_dash_name"); st.selectbox("Idioma", ["Español"], key="cfg_form_lang", index=0, disabled=True)
        try: zones=sorted(pytz.common_timezones); tz_idx=zones.index(tz) if tz in zones else 0; zones.insert(0,tz) if tz not in zones else None; tz_idx=zones.index(tz)
        except: zones=[tz,'America/Bogota']; tz_idx=0
        st.selectbox("Zona Horaria *", zones, index=tz_idx, key="cfg_form_tz")
        st.markdown("---"); submitted = st.form_submit_button("💾 Guardar General", type="primary")
        if submitted:
            errs=[]; n=st.session_state.cfg_form_dash_name; t=st.session_state.cfg_form_tz
            if not n or len(n)<3: errs.append("Nombre corto.")
            if not t: errs.append("Seleccione TZ.")
            if errs:
                 for e in errs: st.error(f"⚠️ {e}")
            else:
                 kvs={'dashboard_name':n,'language':st.session_state.cfg_form_lang,'timezone':t}; ok=True; ems=[]
                 try:
                      with get_db_session() as db:
                           for k,v in kvs.items():
                                if not save_configuration(k,v,'general',db_session=db): ok=False; ems.append(f"'{k}'")
                      if ok: st.success("✅ General guardado."); time.sleep(1); st.rerun()
                      else: st.warning(f"⚠️ Error general: {', '.join(ems)}")
                 except Exception as e: st.error(f"Error fatal general: {e}")

def appearance_config_section(): # Sin cambios
    st.header("Apariencia"); st.caption("Colores y logo.")
    with st.form("appearance_config_form"):
        from utils.styles import get_configured_colors; ic=get_configured_colors(); cks=list(ic.keys())
        st.subheader("Colores"); c1,c2=st.columns(2); nk=len(cks); k1=cks[:nk//2]; k2=cks[nk//2:]
        with c1:
             for k in k1: l=k.replace('color_','').replace('_',' ').title(); st.color_picker(l,value=ic.get(k,'#F'),key=f"cfg_form_{k}")
        with c2:
             for k in k2: l=k.replace('color_','').replace('_',' ').title(); st.color_picker(l,value=ic.get(k,'#0'),key=f"cfg_form_{k}")
        st.markdown("---"); st.subheader("Logo"); lu=get_configuration('logo_url','general',''); st.text_input("URL Logo *",value=lu,key="cfg_form_logo_url")
        if st.session_state.cfg_form_logo_url and st.session_state.cfg_form_logo_url.startswith('http'): st.image(st.session_state.cfg_form_logo_url,width=250)
        st.markdown("---"); submitted=st.form_submit_button("💾 Guardar Apariencia", type="primary")
        if submitted:
             errs=[]; curl=st.session_state.cfg_form_logo_url
             if not curl: errs.append("URL logo obligatoria.")
             elif not curl.startswith(('http://','https://')): errs.append("URL logo inválida.")
             if errs:
                  for e in errs: st.error(f"⚠️ {e}")
             else:
                  ok=True; ems=[]
                  try:
                       with get_db_session() as db:
                            for k in cks:
                                 if not save_configuration(k,st.session_state[f"cfg_form_{k}"],'appearance',db_session=db): ok=False; ems.append(f"'{k}'")
                            if not save_configuration('logo_url',curl,'general',db_session=db): ok=False; ems.append("'logo_url'")
                       if ok: st.success("✅ Apariencia guardada. ¡Refresca (F5)!"); time.sleep(1)
                       else: st.warning(f"⚠️ Error apariencia: {', '.join(ems)}")
                  except Exception as e: st.error(f"Error fatal apariencia: {e}")

def security_config_section(): # Sin cambios
    st.header("Seguridad"); st.caption("Contraseña y sesión.")
    with st.form("security_config_form"):
        from auth.auth import get_security_config_values as gsc; init_sec=gsc()
        st.subheader("Contraseña"); st.number_input("Longitud Mínima *",4,32,init_sec['password_min_length'],1,key="cfg_form_sec_pwd_len"); st.checkbox("Req Mayúsculas",init_sec['password_require_uppercase'],key="cfg_form_sec_pwd_upper"); st.checkbox("Req Números",init_sec['password_require_numbers'],key="cfg_form_sec_pwd_num"); st.checkbox("Req Especiales",init_sec['password_require_special'],key="cfg_form_sec_pwd_spec")
        st.markdown("---"); st.subheader("Sesión"); st.number_input("Timeout (min) *",5,720,init_sec['session_timeout'],5,key="cfg_form_sec_sess_time")
        st.markdown("---"); submitted=st.form_submit_button("💾 Guardar Seguridad", type="primary")
        if submitted:
             kvs={'password_min_length':st.session_state.cfg_form_sec_pwd_len,'password_require_uppercase':st.session_state.cfg_form_sec_pwd_upper,'password_require_numbers':st.session_state.cfg_form_sec_pwd_num,'password_require_special':st.session_state.cfg_form_sec_pwd_spec,'session_timeout':st.session_state.cfg_form_sec_sess_time}
             ok=True; ems=[]
             try:
                 with get_db_session() as db:
                      for k,v in kvs.items():
                           if not save_configuration(k,str(v),'security',db_session=db): ok=False; ems.append(f"'{k}'")
                 if ok: st.success("✅ Config seguridad guardada."); time.sleep(1)
                 else: st.warning(f"⚠️ Error seguridad: {', '.join(ems)}")
             except Exception as e: st.error(f"Error fatal seguridad: {e}")

# --- Ejecutar ---
apply_global_styles()
show_config_page()
