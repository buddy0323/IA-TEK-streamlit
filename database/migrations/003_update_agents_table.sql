-- Agregar nuevas columnas a la tabla agents
ALTER TABLE agents ADD COLUMN description TEXT;
ALTER TABLE agents ADD COLUMN last_connection TIMESTAMP;
ALTER TABLE agents ADD COLUMN model_version TEXT;

-- Actualizar los agentes existentes con información de ejemplo
UPDATE agents SET 
    description = CASE 
        WHEN name = 'Agente Catastro' THEN 'Asistente especializado en consultas catastrales'
        WHEN name = 'Agente Trámites' THEN 'Asistente para gestión de trámites municipales'
        WHEN name = 'Agente Consultas' THEN 'Asistente para consultas generales'
        ELSE 'Asistente IA'
    END,
    last_connection = datetime('now', '-' || (ABS(RANDOM() % 24)) || ' hours'),
    model_version = CASE 
        WHEN name = 'Agente Catastro' THEN 'GPT-4'
        WHEN name = 'Agente Trámites' THEN 'Claude-2'
        WHEN name = 'Agente Consultas' THEN 'GPT-3.5'
        ELSE 'GPT-3.5'
    END;