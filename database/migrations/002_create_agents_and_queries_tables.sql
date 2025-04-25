CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    total_queries INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    avg_response_time REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    query_text TEXT NOT NULL,
    response_time REAL NOT NULL,
    success INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar algunos agentes de ejemplo
INSERT INTO agents (name, status, total_queries, success_rate, avg_response_time) VALUES 
('Agente Catastro', 'active', 150, 95.5, 0.8),
('Agente Trámites', 'active', 200, 88.2, 1.2),
('Agente Consultas', 'inactive', 50, 75.0, 2.0);

-- Insertar algunas consultas de ejemplo para hoy
INSERT INTO queries (agent_id, query_text, response_time, success, created_at) 
SELECT 
    ABS(RANDOM() % 3) + 1 as agent_id,
    'Consulta de ejemplo ' || RANDOM() as query_text,
    RANDOM() + 0.5 as response_time,
    ABS(RANDOM() % 2) as success,
    datetime('now', '-' || (ABS(RANDOM() % 24)) || ' hours', '-' || (ABS(RANDOM() % 60)) || ' minutes')
FROM (SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5);