# --- utils/api_client.py (Simplificado para Agentes Locales) ---

import streamlit as st
import requests
import base64
import json
import logging
from typing import Optional, Tuple, Any, Dict, List

log = logging.getLogger(__name__)

try:
    from utils.config import get_configuration
except ImportError:
    log.error("FATAL: Failed to import get_configuration from utils.config.")
    def get_configuration(key: str, category: Optional[str] = None, default: Optional[Any] = None) -> Optional[str]: return default

# --- Constantes y Configuración ---
N8N_CONFIG_CATEGORY = 'api'
DEFAULT_TIMEOUT_CHAT = 90 # Segundos para chat

# --- Helper para obtener SOLO credenciales N8N ---
def get_n8n_credentials() -> Dict[str, Optional[str]]:
    """Obtiene solo username y password de N8N."""
    creds = {'n8n_username': None, 'n8n_password': None}
    try:
        creds['n8n_username'] = get_configuration('n8n_username', N8N_CONFIG_CATEGORY)
        creds['n8n_password'] = get_configuration('n8n_password', N8N_CONFIG_CATEGORY)
    except Exception as e:
        log.error(f"Failed to retrieve N8N credentials: {e}", exc_info=True)
    return creds

# --- Helper para crear Headers N8N (Sin cambios) ---
def create_n8n_auth_headers(config: Dict[str, Any]) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
    username = config.get('n8n_username'); password = config.get('n8n_password')
    if not username or not password: return None, "Credenciales N8N incompletas."
    try:
        credentials = base64.b64encode(f"{username}:{password}".encode('utf-8')).decode('utf-8')
        headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/json", "Accept": "application/json"}
        return headers, None
    except Exception as e: log.error(f"Error encoding N8N credentials: {e}"); return None, "Error codificando credenciales."

# --- Función Genérica de Request (Sin cambios significativos) ---
def _make_n8n_request(method: str, url: Optional[str], headers: Optional[Dict[str, str]],
                       params: Optional[Dict[str, Any]] = None,
                       data: Optional[Dict[str, Any]] = None,
                       timeout: int = 30) -> Tuple[Optional[Any], Optional[str]]:
    # ... (código idéntico a la versión anterior) ...
    if not url: log.error("N8N request failed: URL missing."); return None, "URL de N8N no proporcionada."
    if not headers: log.error("N8N request failed: Headers missing."); return None, "Headers N8N no disponibles."
    method = method.upper(); log.debug(f"N8N {method} {url}")
    if params: log.debug(f" Params: {params}")
    if data: log.debug(f" Data: {str(data)[:200]}...")
    try:
        response = requests.request(method=method, url=url, headers=headers, params=params, json=data, timeout=timeout)
        log.debug(f"N8N Resp Status: {response.status_code} from {method} {url}")
        response.raise_for_status()
        if response.status_code == 204: log.info(f"N8N {url} 204"); return {"success": True, "status_code": 204}, None
        try: return response.json(), None
        except json.JSONDecodeError:
            response_text = response.text
            if response.ok:
                if not response_text: log.warning(f"N8N {url} OK {response.status_code} empty body."); return {"success": True, "status_code": response.status_code}, None
                else: log.warning(f"N8N {url} OK {response.status_code} non-JSON: {response_text[:100]}..."); return {"success": True, "status_code": response.status_code, "content": response_text}, None
            else: log.error(f"N8N {url} not-OK {response.status_code} non-JSON: {response_text[:200]}..."); return None, f"Respuesta N8N ({response.status_code}) no JSON."
    except requests.exceptions.Timeout: log.error(f"Timeout ({timeout}s) N8N {url}."); return None, f"Timeout ({timeout}s) N8N."
    except requests.exceptions.ConnectionError as e: log.error(f"Conn error N8N {url}: {e}"); return None, f"Error conexión N8N ({url})."
    except requests.exceptions.HTTPError as e:
        err_msg = f"HTTP {e.response.status_code} N8N ({method} {url})."
        try: error_details = e.response.json(); err_msg += f" Det: {error_details.get('message', str(error_details))}"
        except json.JSONDecodeError: err_msg += f" Body: {e.response.text[:200]}"
        log.error(err_msg); return None, err_msg
    except Exception as e: log.error(f"Unexpected error N8N req {url}: {e}", exc_info=True); return None, f"Error inesperado N8N: {e}"


# --- Funciones N8N Eliminadas ---
# Ya no necesitamos: obtener_lista_agentes_n8n, obtener_datos_relacionados_n8n,
# crear_agente_n8n, editar_agente_n8n, eliminar_agente_n8n, test_n8n_connection

# --- Función de Chat (MODIFICADA para recibir URL) ---
def enviar_mensaje_al_agente_n8n(chat_url: Optional[str], message: str, session_id: str) -> Tuple[str, Optional[Any]]:
    """
    Envía un mensaje a una URL de chat N8N específica.
    Requiere credenciales globales de N8N.
    Devuelve (texto_respuesta_procesado, datos_respuesta_completos_o_None).
    """
    log.info(f"Sending message via N8N (Session: {session_id}) to URL: {chat_url}")
    if not chat_url: return "Error: URL de chat no proporcionada para este agente.", None

    # Obtener credenciales globales
    creds = get_n8n_credentials()
    headers, error_headers = create_n8n_auth_headers(creds)
    if error_headers: return f"Error de configuración N8N: {error_headers}", None

    # Payload (Ajustar si N8N necesita algo más que input y session)
    payload = { "sessionId": session_id, "chatInput": message }
    log.debug(f"Chat payload for {chat_url}: {payload}")

    # Realizar la solicitud POST
    response_data, error = _make_n8n_request('POST', chat_url, headers, data=payload, timeout=DEFAULT_TIMEOUT_CHAT)

    # Manejar error en la solicitud
    if error:
        log.error(f"Error sending chat message to N8N URL {chat_url}: {error}")
        return f"Error al contactar al agente ({error})", None

    # Procesar Respuesta Exitosa (lógica de extracción igual que antes)
    log.debug(f"Raw chat response data from N8N URL {chat_url}: {str(response_data)[:500]}")
    response_text = None; possible_keys = ['output', 'response', 'text', 'message', 'result', 'answer', 'content']
    try:
        if isinstance(response_data, dict):
            for key in possible_keys:
                if key in response_data and isinstance(response_data[key], str): response_text = response_data[key]; break
            if response_text is None:
                for sub_key in ['json', 'data']:
                     if sub_key in response_data and isinstance(response_data[sub_key], dict):
                         for key in possible_keys:
                             if key in response_data[sub_key] and isinstance(response_data[sub_key][key], str): response_text = response_data[sub_key][key]; break
                     if response_text: break
        elif isinstance(response_data, list) and len(response_data) > 0:
            first_item = response_data[0]
            if isinstance(first_item, str): response_text = first_item
            elif isinstance(first_item, dict):
                for key in possible_keys:
                    if key in first_item and isinstance(first_item[key], str): response_text = first_item[key]; break
        elif isinstance(response_data, str): response_text = response_data
    except Exception as e: log.error(f"Error processing N8N chat response structure: {e}", exc_info=True); return f"Error al procesar respuesta: {e}", response_data

    if response_text is not None: log.info(f"Extracted chat response from {chat_url}."); return str(response_text), response_data
    else: log.warning(f"Could not extract chat response from {chat_url}."); fallback_msg = f"Respuesta inesperada: {str(response_data)[:150]}..."; return fallback_msg, response_data


# --- Placeholders para otras APIs (sin cambios) ---
def test_agentops_connection(api_key):
    if not api_key: st.error("AgentOps: API Key requerida."); return False
    st.info("AgentOps: Simulación de prueba (valida formato básico).")
    if isinstance(api_key, str) and len(api_key) > 20: st.success("✅ AgentOps: Formato OK."); return True
    else: st.error("❌ AgentOps: Formato inválido."); return False
def test_anthropic_connection(api_key):
    if not api_key: st.error("Anthropic: API Key requerida."); return False
    st.info("Anthropic: Simulación de prueba (valida formato 'sk-ant-...' o similar).")
    if isinstance(api_key, str) and api_key.startswith("sk-ant-") and len(api_key) > 40: st.success("✅ Anthropic: Formato OK."); return True
    else: st.error("❌ Anthropic: Formato inválido."); return False
def test_openai_connection(api_key):
    if not api_key: st.error("OpenAI: API Key requerida."); return False
    st.info("OpenAI: Simulación de prueba (valida formato 'sk-').")
    if isinstance(api_key, str) and api_key.startswith("sk-") and len(api_key) > 40: st.success("✅ OpenAI: Formato OK."); return True
    else: st.error("❌ OpenAI: Formato inválido."); return False
