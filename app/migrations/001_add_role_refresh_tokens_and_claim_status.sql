-- Add user roles (if missing)
ALTER TABLE IF EXISTS users
    ADD COLUMN IF NOT EXISTS role VARCHAR NOT NULL DEFAULT 'user';

-- Refresh tokens table
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR NOT NULL UNIQUE,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    replaced_by_token_hash VARCHAR,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Claim lifecycle fields
ALTER TABLE IF EXISTS claims
    ADD COLUMN IF NOT EXISTS status VARCHAR NOT NULL DEFAULT 'approved',
    ADD COLUMN IF NOT EXISTS review_notes TEXT,
    ADD COLUMN IF NOT EXISTS reviewed_by_user_id INTEGER REFERENCES users(id),
    ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP;
