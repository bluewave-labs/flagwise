-- Migration: Add first_name and last_name columns to users table
-- This script adds name fields to support user profile management

-- Add the new columns
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS first_name VARCHAR(100) DEFAULT '',
ADD COLUMN IF NOT EXISTS last_name VARCHAR(100) DEFAULT '';

-- Update existing admin user to have empty name fields (already defaults to empty)
-- No need to update as DEFAULT '' will handle it

-- Create indexes for name search if needed in the future
-- CREATE INDEX IF NOT EXISTS idx_users_first_name ON users (first_name);
-- CREATE INDEX IF NOT EXISTS idx_users_last_name ON users (last_name);

-- Show the updated table structure
\d users;