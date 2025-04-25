-- Archivo: database/migrations/011_refactor_agents_table.sql
-- Versión Robusta: Recrea la tabla con el esquema final correcto.

PRAGMA foreign_keys=off; -- Desactivar FKs temporalmente

-- 1. Crear la nueva tabla con el esquema CORRECTO Y FINAL
CREATE TABLE agents_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,              -- Nombre único y no nulo
    description TEXT,
    model_name TEXT,                        -- Nueva columna
    skills TEXT,                            -- Nueva columna
    goals TEXT,                             -- Nueva columna
    personality TEXT,                       -- Nueva columna
    status TEXT NOT NULL DEFAULT 'active',  -- Asegurar NOT NULL y default
    n8n_details_url TEXT,                   -- Nueva columna
    n8n_chat_url TEXT,                      -- Nueva columna
    created_at TIMESTAMP,                   -- Mantener timestamp original
    updated_at TIMESTAMP                    -- Nueva columna para timestamp de actualización
);

-- 2. Copiar datos de la tabla vieja a la nueva
--    Seleccionamos SOLO las columnas que esperamos que existan en la tabla vieja
--    y las mapeamos a las nuevas. Usamos COALESCE para defaults si es necesario.
--    ¡IMPORTANTE!: Asumimos que 'id', 'name', 'description', 'status', 'created_at' existen en la tabla vieja.
--                 Si alguna de estas falta en tu tabla 'agents' actual, esta query fallará.
INSERT INTO agents_new (
    id, name, description, model_name, skills, goals, personality, status,
    n8n_details_url, n8n_chat_url, created_at, updated_at
)
SELECT
    id,
    name,
    description,
    NULL, -- model_name (Nueva, sin datos viejos) - O pon un valor default si prefieres
    NULL, -- skills (Nueva)
    NULL, -- goals (Nueva)
    NULL, -- personality (Nueva)
    COALESCE(status, 'active'), -- Usar status viejo o 'active' si era NULL
    NULL, -- n8n_details_url (Nueva)
    NULL, -- n8n_chat_url (Nueva)
    created_at,
    created_at -- Establecer updated_at inicial igual a created_at
FROM
    agents; -- Seleccionar de la tabla 'agents' original

-- 3. Borrar la tabla vieja
DROP TABLE agents;

-- 4. Renombrar la nueva tabla
ALTER TABLE agents_new RENAME TO agents;

-- 5. Recrear índices importantes
CREATE UNIQUE INDEX IF NOT EXISTS ix_agents_name ON agents (name);
CREATE INDEX IF NOT EXISTS ix_agents_status ON agents (status);

PRAGMA foreign_keys=on; -- Reactivar FKs

-- Confirmación (Opcional, solo para verificar en consola)
SELECT 'Migración 011 completada con éxito.' AS status;
