-- Add permissions column to users table
ALTER TABLE users ADD COLUMN permissions TEXT;

-- Delete all existing users
DELETE FROM users;

-- Insert new users with specific permissions
INSERT INTO users (username, password, role, permissions) VALUES 
('superadmin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'superadministrador', 'Vista General, Gestión de agentes IA, Agentes IA, Entrenar, Monitoreo, Historial de Conversaciones, Análisis de Consultas, Gestión de Usuarios, Configuración, Mi Perfil, Roles'),
('admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'administrador', 'Vista General, Gestión de agentes IA, Agentes IA, Entrenar, Monitoreo, Historial de Conversaciones, Análisis de Consultas, Gestión de Usuarios, Mi Perfil, Roles');