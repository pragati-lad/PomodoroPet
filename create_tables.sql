-- PomoPet Database Tables
-- Run this SQL in Supabase SQL Editor to create tables

-- User table
CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE NOT NULL,
    daily_goal INTEGER DEFAULT 60 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_username ON "user"(username);
CREATE INDEX IF NOT EXISTS idx_user_email ON "user"(email);

-- Cat table
CREATE TABLE IF NOT EXISTS cat (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    name VARCHAR(64) NOT NULL,
    cat_type INTEGER NOT NULL,
    age_days INTEGER DEFAULT 0,
    mood VARCHAR(20) DEFAULT 'happy',
    hunger INTEGER DEFAULT 50,
    happiness INTEGER DEFAULT 80,
    size REAL DEFAULT 1.0,
    last_fed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_growth_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Study Session table
CREATE TABLE IF NOT EXISTS study_session (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    focus_duration INTEGER DEFAULT 45,
    break_duration INTEGER DEFAULT 15,
    completed BOOLEAN DEFAULT FALSE,
    focus_score INTEGER DEFAULT 100,
    actual_duration INTEGER,
    camera_enabled BOOLEAN DEFAULT FALSE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
