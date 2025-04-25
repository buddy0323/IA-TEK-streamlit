-- Make role_id nullable in users table
CREATE TABLE users_temp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role_id INTEGER REFERENCES roles(id),
    description TEXT
);

-- Copy data from the old table to the new one
INSERT INTO users_temp SELECT id, username, password, role_id, description FROM users;

-- Drop the old table
DROP TABLE users;

-- Rename the new table to the original name
ALTER TABLE users_temp RENAME TO users;