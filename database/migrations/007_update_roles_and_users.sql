-- Drop the permissions column from users table as it's now in roles
ALTER TABLE users DROP COLUMN permissions;

-- Make sure all users have a valid role_id
UPDATE users SET role_id = (
    SELECT id FROM roles WHERE roles.name = users.role
) WHERE role_id IS NULL;

-- Drop the role column from users as we now use role_id
ALTER TABLE users DROP COLUMN role;