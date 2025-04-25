# --- database/database.py (Corregido Nombre DB y Verificación Esquema) ---

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession
from sqlalchemy.exc import OperationalError
from contextlib import contextmanager
import os
import logging
from typing import Optional

# Importar modelos para que Base los conozca si apply_migrations se usa
from .models import Base

log = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)

# --- Configuración de la Base de Datos (NOMBRE CORREGIDO) ---
try:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # >>>>>>>>> NOMBRE CORREGIDO AQUÍ <<<<<<<<<<
    DB_NAME = "pruebamco_dashboard.db"
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    DATABASE_FILE_PATH = os.path.join(BASE_DIR, DB_NAME)
    DATABASE_URL = f"sqlite:///{DATABASE_FILE_PATH}" # Ruta absoluta Unix

    log.info(f"Attempting connect: {DATABASE_FILE_PATH}")
    log.info(f"SQLAlchemy URL: {DATABASE_URL}")

    if not os.path.exists(DATABASE_FILE_PATH):
        log.error(f"Database file NOT FOUND at specified path: {DATABASE_FILE_PATH}")
        # Considerar crear el archivo/directorio o lanzar un error más informativo
        # os.makedirs(os.path.dirname(DATABASE_FILE_PATH), exist_ok=True) # Solo si se quiere crear directorio
        raise FileNotFoundError(f"DB file not found: {DATABASE_FILE_PATH}")

    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    log.info("SQLAlchemy engine/SessionLocal created.")

    # --- VERIFICACIÓN DE ESQUEMA (Mejorada) ---
    try:
        log.info("Inspecting DB schema via SQLAlchemy inspector...")
        inspector = inspect(engine)
        tables_found = inspector.get_table_names()
        log.info(f"Tables found by inspector: {tables_found}")

        required_tables = ["agents", "agent_options_language_models", "agent_options_skills", "agent_options_personalities", "agent_options_goals", "users", "roles", "configurations", "queries"]
        missing_tables = []
        for table in required_tables:
            if table not in tables_found:
                log.error(f"CRITICAL: Required table '{table}' NOT FOUND via inspector!")
                missing_tables.append(table)

        if not missing_tables:
            log.info("All required tables seem to exist.")
            # Verificar columnas clave si las tablas existen
            if "agents" in tables_found:
                cols = inspector.get_columns('agents'); names = [c['name'] for c in cols]
                if 'model_name' not in names: log.error("CRITICAL: 'model_name' column NOT FOUND in 'agents'!")
                else: log.info("'model_name' column verified in 'agents'.")
            # Añadir más verificaciones de columnas si es necesario
        else:
            log.error(f"Missing critical tables: {', '.join(missing_tables)}. Ensure ALL migrations (001-012) were applied correctly to '{DATABASE_FILE_PATH}'.")

    except Exception as inspect_e:
        log.error(f"Failed to inspect database schema (DB might be locked, corrupted, or path wrong?): {inspect_e}", exc_info=True)
    # --- FIN VERIFICACIÓN ---

except Exception as e_init:
    log.error(f"CRITICAL ERROR DB init: {e_init}", exc_info=True)
    raise RuntimeError(f"Failed DB init: {e_init}") from e_init

# --- Context Manager (Sin cambios) ---
@contextmanager
def get_db_session() -> SQLAlchemySession:
    db: Optional[SQLAlchemySession] = None
    try: db = SessionLocal(); yield db; db.commit()
    except Exception as e: log.error(f"DB transaction rollback: {e}", exc_info=True); db.rollback(); raise
    finally:
        if db: db.close()

# --- Aplicación de Migraciones (Sin cambios en la firma, implementación robusta necesaria) ---
def apply_sqlite_migrations(db_engine, sql_base, migrations_dir="database/migrations"):
     # ... (Usar versión robusta con historial si se activa en app.py) ...
     print(f"INFO: apply_sqlite_migrations called for dir '{migrations_dir}' (ensure implementation is robust).")
     pass
