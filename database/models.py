# --- database/models.py (Añadir Modelos para Opciones) ---

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, ForeignKey, Text, Index, Boolean
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func
from datetime import datetime
import pytz

# Configuración Timezone (con fallback)
try:
    # from utils.config import get_configuration # Evitar import circular aquí
    # TZ_CONFIG = get_configuration('timezone', 'general', 'America/Bogota') or 'America/Bogota'
    colombia_tz = pytz.timezone('America/Bogota') # Usar default seguro
except Exception:
     colombia_tz = pytz.timezone('America/Bogota')

def get_current_time_colombia():
    return datetime.now(colombia_tz)

class Base(DeclarativeBase): pass

class Configuration(Base):
    __tablename__ = 'configurations'; id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False, index=True); value = Column(Text)
    category = Column(String, nullable=False, index=True); description = Column(String)
    created_at = Column(DateTime(timezone=True), default=get_current_time_colombia)
    updated_at = Column(DateTime(timezone=True), default=get_current_time_colombia, onupdate=get_current_time_colombia)
    def __repr__(self): return f"<Configuration(key='{self.key}')>"

class Role(Base):
    __tablename__ = 'roles'; id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False); description = Column(String(255))
    permissions = Column(Text); users = relationship('User', back_populates='role')
    def get_permissions_set(self): return set(p.strip() for p in (self.permissions or '').split(',') if p.strip())
    def __repr__(self): return f"<Role(name='{self.name}')>"

class User(Base):
    __tablename__ = 'users'; id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False, index=True); password = Column(String(64), nullable=False)
    email = Column(String(120), unique=True, nullable=True, index=True); role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    role = relationship('Role', back_populates='users'); description = Column(String(255))
    status = Column(String(10), default='active', nullable=False); created_at = Column(DateTime(timezone=True), default=get_current_time_colombia)
    last_access = Column(DateTime(timezone=True)); __table_args__ = (Index('ix_user_status', 'status'),)
    def __repr__(self): return f"<User(username='{self.username}')>"

# --- Modelo Agent (Sin cambios estructurales necesarios, usará TEXT para almacenar selecciones) ---
class Agent(Base):
    __tablename__ = 'agents'; id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    model_name = Column(Text) # Almacena el nombre del modelo seleccionado
    skills = Column(Text) # Almacena JSON string de nombres de skills seleccionadas
    goals = Column(Text) # Almacena JSON string de nombres de objetivos seleccionados
    personality = Column(Text) # Almacena JSON string de nombres de personalidades seleccionadas
    status = Column(String(20), nullable=False, default='active', index=True)
    n8n_details_url = Column(String(512)); n8n_chat_url = Column(String(512))
    created_at = Column(DateTime(timezone=True), default=get_current_time_colombia)
    updated_at = Column(DateTime(timezone=True), default=get_current_time_colombia, onupdate=get_current_time_colombia)
    queries = relationship('Query', back_populates='agent', cascade="all, delete-orphan", passive_deletes=True)
    def __repr__(self): return f"<Agent(id={self.id}, name='{self.name}')>"

class Query(Base):
    __tablename__ = 'queries'; id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id', ondelete='CASCADE'), nullable=False, index=True)
    session_id = Column(String(36), index=True); query_text = Column(Text, nullable=False); response_text = Column(Text)
    response_time_ms = Column(Integer); success = Column(Boolean, nullable=False, default=True); feedback_score = Column(Integer); error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=get_current_time_colombia)
    agent = relationship('Agent', back_populates='queries')
    def __repr__(self): return f"<Query(id={self.id}, agent_id={self.agent_id})>"

# --- NUEVOS MODELOS PARA OPCIONES DE AGENTE ---

class AgentOptionBase(Base):
    """Clase base abstracta para opciones con ID y Nombre únicos."""
    __abstract__ = True # No crear tabla para esta clase base
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True) # Descripción opcional
    created_at = Column(DateTime(timezone=True), default=get_current_time_colombia)

    def __repr__(self): return f"<{self.__class__.__name__}(name='{self.name}')>"

class LanguageModelOption(AgentOptionBase):
    """Opciones para Modelos de Lenguaje."""
    __tablename__ = 'agent_options_language_models'

class SkillOption(AgentOptionBase):
    """Opciones para Habilidades."""
    __tablename__ = 'agent_options_skills'

class PersonalityOption(AgentOptionBase):
    """Opciones para Personalidades."""
    __tablename__ = 'agent_options_personalities'

class GoalOption(AgentOptionBase):
    """Opciones para Objetivos."""
    __tablename__ = 'agent_options_goals'
