# --- utils/config.py (CORRECTO - Sin importación circular) ---

from sqlalchemy.orm import Session as SQLAlchemySession
from typing import Optional, Any, Dict
from datetime import datetime
import pytz

# Importaciones locales SOLO de database
from database.database import get_db_session # Context manager para obtener sesión
from database.models import Configuration
# !! NO DEBE HABER 'from auth.auth import ...' AQUÍ !!

# --- Configuración de Timezone (con fallback seguro) ---
try:
    # Default seguro, la config real se lee dinámicamente
    DEFAULT_TIMEZONE_CONFIG = 'America/Bogota'
    colombia_tz = pytz.timezone(DEFAULT_TIMEZONE_CONFIG)
except pytz.exceptions.UnknownTimeZoneError:
    print(f"WARN: Default timezone '{DEFAULT_TIMEZONE_CONFIG}' failed? Using 'America/Bogota'.")
    colombia_tz = pytz.timezone('America/Bogota')

# --- Funciones Principales ---

def get_configuration(key: str, category: Optional[str] = None, default: Optional[Any] = None, db_session: Optional[SQLAlchemySession] = None) -> Optional[str]:
    """
    Obtiene un valor de configuración de la base de datos como string.
    """
    session_manager = get_db_session() if db_session is None else db_session
    try:
        if db_session is None:
            with session_manager as db:
                query = db.query(Configuration.value).filter(Configuration.key == key)
                if category: query = query.filter(Configuration.category == category)
                config_value = query.scalar()
        else:
            db = session_manager
            query = db.query(Configuration.value).filter(Configuration.key == key)
            if category: query = query.filter(Configuration.category == category)
            config_value = query.scalar()
        return config_value if config_value is not None else default
    except Exception as e:
        print(f"ERROR getting configuration for key='{key}', category='{category}': {e}")
        return default

def save_configuration(key: str, value: Any, category: str, description: Optional[str] = None, db_session: Optional[SQLAlchemySession] = None) -> bool:
    """
    Guarda o actualiza un valor de configuración en la base de datos.
    """
    value_str = str(value) if value is not None else ''
    session_manager = get_db_session() if db_session is None else db_session
    saved_successfully = False
    try:
        current_time = datetime.now(colombia_tz)
        if db_session is None:
            with session_manager as db:
                config = db.query(Configuration).filter(Configuration.key == key).first()
                if config: # Actualizar
                    if config.value != value_str or config.category != category or (description is not None and config.description != description):
                        config.value = value_str; config.category = category
                        if description is not None: config.description = description
                        config.updated_at = current_time; saved_successfully = True
                    else: saved_successfully = True # No cambios, pero OK
                else: # Crear
                    config = Configuration(key=key, value=value_str, category=category, description=description, created_at=current_time, updated_at=current_time)
                    db.add(config); saved_successfully = True
        else: # Usar sesión externa
            db = session_manager
            config = db.query(Configuration).filter(Configuration.key == key).first()
            if config:
                if config.value != value_str or config.category != category or (description is not None and config.description != description):
                    config.value = value_str; config.category = category
                    if description is not None: config.description = description
                    config.updated_at = current_time; saved_successfully = True
                else: saved_successfully = True
            else:
                config = Configuration(key=key, value=value_str, category=category, description=description, created_at=current_time, updated_at=current_time)
                db.add(config); saved_successfully = True
        return saved_successfully
    except Exception as e:
        print(f"ERROR saving configuration for key='{key}': {e}")
        return False

def get_all_configurations(db_session: Optional[SQLAlchemySession] = None) -> Dict[str, str]:
    """Obtiene todas las configuraciones como un diccionario {key: value_str}."""
    session_manager = get_db_session() if db_session is None else db_session
    configs: Dict[str, str] = {}
    try:
        if db_session is None:
            with session_manager as db: all_configs_db = db.query(Configuration).all()
        else: db = session_manager; all_configs_db = db.query(Configuration).all()
        for config_db in all_configs_db: configs[config_db.key] = config_db.value or ''
    except Exception as e: print(f"Error getting all configurations: {e}")
    return configs
