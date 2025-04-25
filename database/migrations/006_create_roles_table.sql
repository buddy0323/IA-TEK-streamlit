-- Create roles table
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    permissions TEXT
);

-- Insert default roles
INSERT INTO roles (name, description, permissions) VALUES 
('superadministrador', 'Usuario con acceso total al sistema', 'Vista General, Gestión de agentes IA, Agentes IA, Entrenar, Monitoreo, Historial de Conversaciones, Análisis de Consultas, Gestión de Usuarios, Configuración, Mi Perfil, Roles'),
('administrador', 'Usuario con acceso administrativo', 'Vista General, Gestión de agentes IA, Agentes IA, Entrenar, Monitoreo, Historial de Conversaciones, Análisis de Consultas, Gestión de Usuarios, Mi Perfil, Roles'),
('analista', 'Usuario con acceso limitado', 'Vista General, Mi Perfil');

-- Update users table to reference roles table
ALTER TABLE users ADD COLUMN role_id INTEGER REFERENCES roles(id);

-- Update existing users to reference roles
UPDATE users SET role_id = (SELECT id FROM roles WHERE roles.name = users.role);