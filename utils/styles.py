import streamlit as st
from typing import Dict
from utils.config import get_configuration
# Importar get_configuration y get_db_session para leer colores
from database.database import get_db_session # Para optimizar lectura de colores
from database.models import Configuration # Importar el modelo Configuration

# --- Obtención de Colores de Configuración ---
def get_configured_colors() -> Dict[str, str]:
    """Obtiene la paleta de colores desde la configuración con defaults."""
    # Defaults razonables si no están en la BD
    defaults = {
        'color_navbar_bg': '#478C3C',            # Verde oscuro AMCO (ejemplo)
        'color_navbar_text': '#FFFFFF',           # Blanco
        'color_button_primary_bg': '#478C3C',     # Verde primario AMCO
        'color_button_primary_text': '#FFFFFF',   # Blanco
        'color_button_primary_hover_bg': '#3B7031', # Verde más oscuro para hover
        'color_sidebar_bg': '#F0F2F6',            # Gris claro suave
        'color_sidebar_text': '#1E1E1E',           # Texto oscuro en sidebar
        'color_base_bg': '#FFFFFF',               # Fondo principal blanco
        'color_base_text': '#1E1E1E',           # Texto principal oscuro
        'color_widget_border': '#CCCCCC',         # Borde gris claro para widgets
        'color_table_header': '#F0F2F6',          # Fondo cabecera tabla (como sidebar)
        'color_link': '#0068C9',                # Azul estándar para links
    }
    colors = defaults.copy()
    try:
        # Leer todas las claves de color de la categoría 'appearance' en una sola consulta
        all_appearance_configs = {}
        with get_db_session() as db:
             configs_db = db.query(Configuration).filter(Configuration.category == 'appearance').all()
             all_appearance_configs = {c.key: c.value for c in configs_db}

        for key in defaults:
             value = all_appearance_configs.get(key) # Buscar en lo leído de DB
             if value and isinstance(value, str) and value.startswith('#') and len(value) in [4, 7]:
                  colors[key] = value
             # Si no está en DB o el valor no es válido, se mantiene el default
             # else: colors[key] = defaults[key] # Ya está en colors por el copy()

    except Exception as e:
        print(f"ERROR reading color configuration: {e}. Using defaults.")
        colors = defaults.copy() # Asegurar defaults en caso de error mayor

    # Asegurar que el hover no esté vacío si el primario sí está
    if not colors.get('color_button_primary_hover_bg') and colors.get('color_button_primary_bg'):
        colors['color_button_primary_hover_bg'] = colors['color_button_primary_bg']

    return colors

# --- Generación de CSS ---

def generate_css_variables(colors: Dict[str, str]) -> str:
    """Genera variables CSS a partir de la paleta de colores."""
    # Generar variables CSS a partir del diccionario de colores
    css_vars_lines = [f"    --{key.replace('color_', '').replace('_', '-')}: {value};" for key, value in colors.items()]
    return f"""
    :root {{
{chr(10).join(css_vars_lines)}
    }}
    """

def load_base_css() -> str:
    """Devuelve el CSS base y estilos generales usando variables CSS."""
    css = f"""
        <style>
            /* === Base Styles === */
            body {{
                color: var(--base-text);
                background-color: var(--base-bg); /* Aplicar fondo base al body también */
                font-family: 'Source Sans Pro', sans-serif; /* Fuente más limpia */
            }}
            .stApp {{
                background-color: var(--base-bg) !important;
            }}

            /* === [INICIO ÚLTIMO INTENTO CSS] OCULTAR NAVEGACIÓN AUTOMÁTICA === */
            /* Simplifica el selector y añade más propiedades para forzar ocultación */
            div[data-testid="stSidebarNav"] {{
                display: none !important;
                visibility: hidden !important;
                height: 0px !important;         /* Forzar altura 0 */
                width: 0px !important;          /* Forzar ancho 0 */
                overflow: hidden !important;    /* Ocultar contenido desbordado */
                margin: 0 !important;           /* Quitar márgenes */
                padding: 0 !important;          /* Quitar padding */
                border: none !important;        /* Quitar bordes */
                position: absolute !important;  /* Sacarlo del flujo normal (agresivo) */
                left: -9999px !important;       /* Moverlo fuera de la pantalla */
            }}
            /* === [FIN ÚLTIMO INTENTO CSS] ==================================== */

            /* Text color para elementos comunes */
            .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6,
            label, .stCheckbox > label span, .stRadio > label span,
            .stTextInput > label, .stSelectbox > label, .stTextArea > label,
            .stNumberInput > label, .stDateInput > label, .stTimeInput > label,
            .stMultiSelect > label, .stColorPicker > label, .stFileUploader > label,
            div[data-baseweb="select"] > div, /* Placeholder/valor en Selectbox */
            button /* Estilo base botones */
            {{
                color: var(--base-text) !important;
                font-family: 'Source Sans Pro', sans-serif !important;
            }}
            h1, h2, h3 {{ font-weight: 600; }} /* Títulos más definidos */

            /* Input field styling */
            .stTextInput input, .stTextArea textarea,
            .stSelectbox div[data-baseweb="select"] > div,
            .stDateInput input, .stTimeInput input,
            .stNumberInput input,
            div[data-testid="stColorPicker"] input /* Input del color picker */
            {{
                color: var(--base-text) !important;
                background-color: var(--base-bg) !important;
                border: 1px solid var(--widget-border) !important;
                border-radius: 4px !important; /* Bordes redondeados suaves */
                transition: border-color 0.2s ease, box-shadow 0.2s ease;
            }}
            .stTextInput input:focus, .stTextArea textarea:focus,
            .stSelectbox div[data-baseweb="select"] > div:focus-within, /* Aproximación para focus */
            .stDateInput input:focus, .stTimeInput input:focus,
            .stNumberInput input:focus
            {{
                 border-color: var(--button-primary-bg) !important; /* Resaltar borde con color primario */
                 box-shadow: 0 0 0 2px rgba(var(--button-primary-bg-rgb, 71, 140, 60), 0.2); /* Añadir un brillo suave */
                 /* Necesitaría convertir HEX a RGB para rgba, o usar un color fijo */
            }}

            /* Placeholder text color */
            .stTextInput input::placeholder, .stTextArea textarea::placeholder {{
                color: #999999 !important;
            }}

            /* Dataframe / Table styling */
            .stDataFrame, .stTable {{
                 border: 1px solid var(--widget-border);
                 border-radius: 6px; /* Más redondeado */
                 overflow: hidden; /* Para que el border-radius funcione */
            }}
            .stDataFrame *, .stTable * {{
                 color: var(--base-text) !important;
                 border: none !important; /* Quitar bordes internos por defecto */
                 font-size: 0.95em; /* Ligeramente más pequeño */
            }}
            .stDataFrame thead th, .stTable thead th {{
                 background-color: var(--table-header-bg) !important;
                 font-weight: 600;
                 color: var(--base-text) !important;
                 border-bottom: 2px solid var(--widget-border) !important; /* Línea más gruesa */
                 padding: 0.75rem 0.6rem !important;
                 text-align: left;
                 white-space: nowrap; /* Evitar wrap en cabecera */
            }}
            .stDataFrame tbody td, .stTable tbody td {{
                 padding: 0.6rem 0.6rem !important; /* Ajustar padding celdas */
                 border-bottom: 1px solid #EEEEEE; /* Líneas suaves entre filas */
                 vertical-align: middle; /* Alinear verticalmente */
            }}
            .stDataFrame tbody tr:last-child td, .stTable tbody tr:last-child td {{
                 border-bottom: none; /* Sin borde en la última fila */
            }}
            .stDataFrame tbody tr:nth-child(even), .stTable tbody tr:nth-child(even) {{
                background-color: #FAFAFA; /* Fondo filas pares más sutil */
            }}
            .stDataFrame tbody tr:hover, .stTable tbody tr:hover {{
                background-color: #F0F0F0; /* Hover sutil */
            }}

            /* Links */
            a, a:visited {{ color: var(--link-color) !important; text-decoration: none; font-weight: 500;}}
            a:hover {{ text-decoration: underline; }}

            /* Hide Streamlit elements */
            footer, #MainMenu {{ display: none !important; visibility: hidden !important; }}

            /* Main content padding */
             .main .block-container {{
                 padding-top: calc(3.75rem + 1.5rem); /* Navbar height + espacio extra */
                 padding-bottom: 3rem;
                 padding-left: 2.5rem;
                 padding-right: 2.5rem;
             }}

             /* Sidebar Styling */
             section[data-testid="stSidebar"] {{
                background-color: var(--sidebar-bg) !important;
                border-right: 1px solid #E0E0E0; /* Borde derecho sutil */
             }}
             section[data-testid="stSidebar"] * {{ color: var(--sidebar-text) !important; }}
             section[data-testid="stSidebar"] .stRadio label span,
             section[data-testid="stSidebar"] .stCheckbox label span
             {{ color: var(--sidebar-text) !important; }}
             /* Centrar logo sidebar */
             section[data-testid="stSidebar"] div[data-testid="stImage"] {{
                 text-align: center; padding: 1rem 0;
             }}
             section[data-testid="stSidebar"] div[data-testid="stImage"] img {{
                 max-width: 70%; height: auto; /* Ajustar tamaño logo */
             }}
             section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {{
                  gap: 0.5rem; /* Espacio entre elementos */
             }}
             section[data-testid="stSidebar"] h3 {{ /* Títulos en Sidebar */
                 font-size: 1.1em; font-weight: 600; margin-top: 1rem; margin-bottom: 0.5rem;
                 color: var(--sidebar-text) !important; opacity: 0.9;
             }}

             /* Dialog Styling (para st.dialog) */
             div[data-testid="stDialog"] > div {{
                background-color: var(--base-bg);
                border-radius: 8px;
                border: 1px solid #D0D0D0; /* Borde ligeramente más oscuro */
                box-shadow: 0 8px 20px rgba(0,0,0,0.12); /* Sombra más pronunciada */
                padding: 1.5rem 2rem; /* Más padding horizontal */
             }}
             div[data-testid="stDialog"] h1, /* Título */
             div[data-testid="stDialog"] h2,
             div[data-testid="stDialog"] h3 {{
                color: var(--base-text) !important;
                margin-bottom: 1.2rem; /* Más espacio bajo título */
                font-weight: 600;
             }}

             /* Mejoras botones generales */
             .stButton > button {{
                 border-radius: 5px !important;
                 padding: 0.6rem 1.2rem !important; /* Más padding */
                 font-weight: 500 !important; /* Ligeramente más grueso */
                 transition: all 0.2s ease !important;
             }}
             .stButton > button:hover {{
                 transform: translateY(-2px); /* Efecto hover más notorio */
                 box-shadow: 0 5px 10px rgba(0,0,0,0.1) !important;
             }}
             .stButton > button:active {{
                 transform: translateY(0px);
                 box-shadow: inset 0 2px 4px rgba(0,0,0,0.1) !important;
             }}
             /* Asegurar estilo similar para botón de descarga */
             .stDownloadButton > button {{
                 border-radius: 5px !important;
                 padding: 0.6rem 1.2rem !important;
                 font-weight: 500 !important;
             }}

             /* Estilos para tabs */
             div[data-baseweb="tab-list"] button[role="tab"] {{
                 padding: 0.8rem 1rem !important;
                 font-weight: 500 !important;
                 color: #555 !important;
             }}
             div[data-baseweb="tab-list"] button[role="tab"][aria-selected="true"] {{
                 color: var(--button-primary-bg) !important; /* Color primario para tab activa */
                 border-bottom-color: var(--button-primary-bg) !important;
             }}


        </style>
    """
    return css

def get_navbar_css() -> str:
    """Genera el CSS para la barra de navegación superior fija."""
    # Usa variables CSS definidas globalmente
    return f"""
        <style>
            /* === Navbar Styles === */
            .navbar-container {{
                position: fixed !important; top: 0 !important; left: 0 !important;
                right: 0 !important; height: 3.75rem !important; /* 60px */
                background-color: var(--navbar-bg) !important;
                color: var(--navbar-text) !important;
                display: flex !important; align-items: center !important;
                justify-content: center !important; /* Centrar título */
                padding: 0 1.5rem !important;
                z-index: 1000 !important; /* Asegurar que esté sobre otros elementos */
                box-shadow: 0 2px 5px rgba(0,0,0,0.1); /* Sombra suave */
            }}
            .navbar-title {{
                font-size: 1.5rem !important;
                font-weight: 600 !important;
                color: var(--navbar-text) !important;
                margin: 0;
                line-height: 3.75rem; /* Alinear verticalmente */
                letter-spacing: 0.5px;
            }}
        </style>
    """

def get_button_css() -> str:
     """Genera CSS para botones primarios y secundarios usando variables."""
     # Asegura que los estilos de botón primario y secundario se apliquen correctamente
     return f"""
     <style>
        /* === Button Styles === */

        /* --- Primary Button --- */
        /* Target default button and explicitly primary buttons */
        .stButton > button:not([kind="secondary"]):not([kind="header"]):not([kind="minimal"]):not([kind="toolbar"]),
        .stDownloadButton > button:not([kind="secondary"]):not([kind="header"]):not([kind="minimal"]):not([kind="toolbar"]),
        .stFormSubmitButton > button /* Form submit button */
        {{
            background-color: var(--button-primary-bg) !important;
            color: var(--button-primary-text) !important;
            border: 1px solid var(--button-primary-bg) !important; /* Borde del mismo color */
        }}
        .stButton > button:not([kind="secondary"]):not([kind="header"]):not([kind="minimal"]):not([kind="toolbar"]):hover,
        .stDownloadButton > button:not([kind="secondary"]):not([kind="header"]):not([kind="minimal"]):not([kind="toolbar"]):hover,
        .stFormSubmitButton > button:hover
        {{
            background-color: var(--button-primary-hover-bg) !important;
            border-color: var(--button-primary-hover-bg) !important;
            /* Sombra y transform ya aplicados por estilo base de botón */
        }}
        /* Estilo Active (cuando se hace clic) */
        .stButton > button:not([kind="secondary"]):not([kind="header"]):not([kind="minimal"]):not([kind="toolbar"]):active,
        .stDownloadButton > button:not([kind="secondary"]):not([kind="header"]):not([kind="minimal"]):not([kind="toolbar"]):active,
        .stFormSubmitButton > button:active
        {{
             background-color: var(--button-primary-hover-bg) !important;
             border-color: var(--button-primary-hover-bg) !important;
             /* Sombra inset ya aplicada por estilo base */
        }}
        /* Estilo Deshabilitado */
        .stButton > button:not([kind="secondary"]):disabled,
        .stDownloadButton > button:not([kind="secondary"]):disabled,
        .stFormSubmitButton > button:disabled
         {{
            background-color: #CCCCCC !important;
            color: #888888 !important;
            border-color: #CCCCCC !important;
            cursor: not-allowed !important;
            transform: none !important;
            box-shadow: none !important;
        }}

        /* --- Secondary Button --- */
         .stButton > button[kind="secondary"] {{
             background-color: var(--base-bg) !important; /* Fondo base (blanco) */
             color: var(--base-text) !important; /* Texto base */
             border: 1px solid var(--widget-border) !important; /* Borde widget */
         }}
         .stButton > button[kind="secondary"]:hover {{
             background-color: #F8F9FA !important; /* Gris muy claro */
             border-color: #ADB5BD !important;
             color: var(--base-text) !important; /* Mantener color texto */
         }}
          .stButton > button[kind="secondary"]:active {{
              background-color: #E9ECEF !important; /* Gris un poco más oscuro */
              border-color: #ADB5BD !important;
          }}
         .stButton > button[kind="secondary"]:disabled {{
             background-color: #F8F9FA !important; /* Fondo claro */
             color: #ADB5BD !important; /* Texto gris claro */
             border-color: #CED4DA !important;
             cursor: not-allowed !important;
         }}

         /* Botón de Cerrar Sesión en Sidebar */
         /* Debe ser un botón normal para heredar estilo primario */
         section[data-testid="stSidebar"] .stButton > button {{
             width: 100% !important;
             margin-top: 1.5rem !important; /* Más espacio arriba */
             /* Heredará el estilo primario (verde/rojo según config) */
         }}
     </style>
     """

def get_login_page_style() -> str:
     """
     Genera el CSS específico para la página de login.
     Usa colores fijos (verde #478C3C) según lo solicitado para esta página.
     ¡¡El selector CSS para la caja de login ('login_box_selector') sigue siendo CRÍTICO!!
     """
     # Obtener colores base (para fondo, etc.) pero usar colores específicos para elementos del login
     colors = get_configured_colors()
     login_primary_color = "#478C3C" # Verde específico login
     login_button_hover_bg = "#3B7031" # Verde oscuro específico login

     # ====================================================================
     # === SELECTOR CSS PARA LA CAJA DE LOGIN (st.container)            ===
     # ====================================================================
     # !!! --- ¡¡¡ AJUSTA ESTE SELECTOR INSPECCIONANDO EL HTML !!! --- !!!
     # Busca el 'div' que envuelve el H3 'AMCO Dashboard', el subtítulo y el form.
     # Ejemplo basado en estructura común de Streamlit:
     login_box_selector = '.main div[data-testid="stVerticalBlock"]:has(>.stForm)'
     # Otros intentos si el anterior falla:
     # login_box_selector = '.main .block-container>div>div>div[data-testid="stVerticalBlock"]' # Más genérico
     # login_box_selector = '.st-emotion-cache-xxxxxx' # Si encuentras clase específica
     # ====================================================================

     # Selector para el botón DENTRO de la caja
     login_button_selector = f'{login_box_selector} form[data-testid="stForm"] div[data-testid="stFormSubmitButton"] > button'

     return f"""
     <style>
         /* === Login Page Specific Styles === */
         /* 1. Ocultar Navbar y Sidebar */
         .navbar-container, section[data-testid="stSidebar"] {{ display: none !important; visibility: hidden !important; }}
         /* 2. Fondo y Padding */
         body, .stApp {{ background-color: var(--base-bg) !important; }}
         .main .block-container {{ padding: 1rem !important; max-width: 100% !important; }}
         /* 3. Estilos Header Login */
         div[data-testid="stImage"] {{ text-align: center; margin-bottom: 1rem; }}
         h2.login-header-title {{ text-align: center; color: {login_primary_color} !important; font-size: 1.8em; font-weight: 600; margin-top: 0; margin-bottom: 0.25rem; }}
         p.login-header-subtitle {{ text-align: center; color: #555555 !important; font-size: 0.95em; margin-bottom: 0; }}

         /* --- 4. CAJA DE LOGIN --- */
         /* !!! AJUSTA '{login_box_selector}' SI ES NECESARIO !!! */
         {login_box_selector} {{
             display: block !important; width: 100% !important;
             max-width: 450px !important; /* Ancho fijo */
             margin: 2.5rem auto 0 auto !important; /* Centrado H y margen superior */
             padding: 2.5rem 2.5rem !important; /* Padding uniforme */
             background: var(--base-bg) !important;
             border: 1px solid #DCDCDC !important; /* Borde más sutil */
             border-radius: 10px !important; /* Más redondeado */
             box-shadow: 0 6px 18px rgba(0,0,0,0.09) !important; /* Sombra más definida */
         }}
         /* Aplicar color texto base a hijos de la caja */
         {login_box_selector} * {{
              color: var(--base-text) !important;
              font-family: 'Source Sans Pro', sans-serif !important;
         }}

         /* 5. Títulos DENTRO de la caja */
         {login_box_selector} h3.login-box-title {{ text-align: center; font-size: 1.5em; font-weight: 600; margin-bottom: 0.5rem; color: var(--base-text) !important; }}
         {login_box_selector} p.login-box-subtitle {{ text-align: center; color: #6c757d !important; font-size: 0.9em; margin-bottom: 2rem; }}

         /* 6. Inputs DENTRO de la caja */
         {login_box_selector} div[data-testid="stTextInput"] input {{
            border: 1px solid #CED4DA !important; border-radius: 5px !important;
            background-color: #FFFFFF !important; color: var(--base-text) !important;
            padding: 0.9rem 1rem !important; /* Más padding vertical */
            width: 100%; font-size: 1em;
         }}
         {login_box_selector} div[data-testid="stTextInput"] input::placeholder {{ color: #AAAAAA !important; }}
         {login_box_selector} div[data-testid="stTextInput"] input:focus {{
              border-color: {login_primary_color} !important;
              box-shadow: 0 0 0 2px rgba(71, 140, 60, 0.2) !important; /* Brillo verde */
         }}


         /* 7. Botón DENTRO de la caja (VERDE) */
         {login_button_selector} {{
             background: {login_primary_color} !important;
             color: #FFFFFF !important;
             font-weight: 600 !important; font-size: 1em !important;
             border: none !important; border-radius: 6px !important;
             padding: 0.8rem 1.5rem !important; width: 100% !important;
             margin-top: 1rem !important; /* Espacio sobre botón */
             transition: all 0.2s ease !important;
             cursor: pointer !important;
             box-shadow: 0 3px 6px rgba(0,0,0,0.1) !important;
         }}
         {login_button_selector}:hover {{
             background: {login_button_hover_bg} !important;
             box-shadow: 0 5px 10px rgba(0,0,0,0.2) !important; transform: translateY(-2px);
         }}
         {login_button_selector}:active {{
             background-color: {login_button_hover_bg} !important; box-shadow: inset 0 2px 4px rgba(0,0,0,0.15) !important; transform: translateY(0px);
         }}
         {login_button_selector}:focus {{ outline: none !important; box-shadow: 0 0 0 3px rgba(71, 140, 60, 0.3) !important; }} /* Focus visible */
         {login_button_selector}:disabled {{
            background: #B0D1AB !important; color: #F0F0F0 !important; cursor: not-allowed !important;
            box-shadow: none !important; transform: none !important;
         }}

         /* 8. Error Alert DENTRO de la caja */
         {login_box_selector} div[data-testid="stAlert"] {{
            background-color: #f8d7da !important; color: #721c24 !important;
            border: 1px solid #f5c6cb !important; border-radius: 5px; width: 100%;
            margin-top: 1.5rem; padding: 0.9rem 1rem !important;
            text-align: center; font-size: 0.9em;
         }}

         /* 9. Ocultar Footer global */
         footer {{ display: none !important; visibility: hidden !important; }}
     </style>
     """

# --- Funciones Principales para Aplicar Estilos ---
def apply_global_styles():
    # ... (código existente en tu apply_global_styles) ...
    try:
        # ... (lectura de colores) ...
        st.markdown(f"<style>{generate_css_variables(colors)}</style>", unsafe_allow_html=True)
        # --- Carga el CSS modificado ---
        st.markdown(load_base_css(), unsafe_allow_html=True)
        # --- Fin ---
        st.markdown(get_navbar_css(), unsafe_allow_html=True)
        st.markdown(get_button_css(), unsafe_allow_html=True)
    except Exception as e:
        # ... (manejo de error existente) ...
        st.markdown(load_base_css(), unsafe_allow_html=True)

def show_navbar():
    """Muestra la barra de navegación superior fija usando estilos globales."""
    dashboard_name = get_configuration('dashboard_name', 'general', 'IA-AMCO Dashboard') or "IA-AMCO"
    st.markdown(f'<div class="navbar-container"><span class="navbar-title">{dashboard_name}</span></div>', unsafe_allow_html=True)
