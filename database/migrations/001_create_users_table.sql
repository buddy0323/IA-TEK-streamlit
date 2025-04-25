CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL
);

-- Insertar usuarios de ejemplo
INSERT OR IGNORE INTO users (username, password, role) VALUES 
('admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'administrador'),
('analista', '33704d0661e8883dd3d903e12f1e29814e390c8f657937026cca1dd84f5bec67', 'analista');