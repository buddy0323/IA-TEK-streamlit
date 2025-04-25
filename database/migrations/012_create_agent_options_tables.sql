-- Archivo: database/migrations/012_create_agent_options_tables.sql

PRAGMA foreign_keys=off; -- Seguridad al crear tablas

-- Crear tabla para opciones de Modelos de Lenguaje
CREATE TABLE IF NOT EXISTS agent_options_language_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_agent_options_language_models_name ON agent_options_language_models (name);

-- Crear tabla para opciones de Habilidades
CREATE TABLE IF NOT EXISTS agent_options_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_agent_options_skills_name ON agent_options_skills (name);

-- Crear tabla para opciones de Personalidades
CREATE TABLE IF NOT EXISTS agent_options_personalities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_agent_options_personalities_name ON agent_options_personalities (name);

-- Crear tabla para opciones de Objetivos
CREATE TABLE IF NOT EXISTS agent_options_goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_agent_options_goals_name ON agent_options_goals (name);

PRAGMA foreign_keys=on; -- Reactivar FKs

-- Insertar valores iniciales (IGNORAR si ya existen)
INSERT OR IGNORE INTO agent_options_language_models (name, description) VALUES
('gpt-3.5-turbo', 'Modelo OpenAI económico'), ('gpt-4', 'Modelo OpenAI avanzado'), ('gpt-4-turbo', 'Modelo OpenAI avanzado/rápido'),
('claude-2', 'Modelo Anthropic v2'), ('claude-3-opus-20240229', 'Modelo Anthropic avanzado (Opus)');
INSERT OR IGNORE INTO agent_options_skills (name) VALUES
('Responder preguntas'), ('Generar resúmenes'), ('Traducir idiomas'), ('Completar formularios'), ('Generar documentos'),
('Realizar cálculos'), ('Proporcionar información legal'), ('Ofrecer asistencia en la navegación');
INSERT OR IGNORE INTO agent_options_personalities (name) VALUES ('Formal'), ('Informal'), ('Amigable'), ('Directo'), ('Empático');
INSERT OR IGNORE INTO agent_options_goals (name) VALUES
('Asistir en consultas catastrales'), ('Facilitar trámites online'), ('Proporcionar información legal'),
('Mejorar eficiencia interna'), ('Automatizar tareas'), ('Reducir carga laboral'), ('Brindar servicio 24/7');

SELECT 'Migración 012 (Crear tablas opciones) ejecutada.' AS status;
