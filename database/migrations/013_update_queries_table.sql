-- Add missing columns to queries table
PRAGMA foreign_keys=off;

-- Create new table with updated schema
CREATE TABLE queries_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    session_id TEXT,
    query_text TEXT NOT NULL,
    response_text TEXT,
    response_time_ms INTEGER,
    success INTEGER NOT NULL,
    feedback_score INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Copy data from old table
INSERT INTO queries_new (
    id, agent_id, query_text, response_time_ms, success, created_at
)
SELECT 
    id, 
    agent_id, 
    query_text, 
    response_time * 1000, -- Convert seconds to milliseconds
    success,
    created_at
FROM queries;

-- Drop old table
DROP TABLE queries;

-- Rename new table
ALTER TABLE queries_new RENAME TO queries;

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_queries_agent_id ON queries (agent_id);
CREATE INDEX IF NOT EXISTS ix_queries_session_id ON queries (session_id);
CREATE INDEX IF NOT EXISTS ix_queries_created_at ON queries (created_at);

PRAGMA foreign_keys=on;

SELECT 'Migración 013 (Actualizar tabla queries) ejecutada.' AS status; 