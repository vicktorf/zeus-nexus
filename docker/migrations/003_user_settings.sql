-- Migration: Add user_settings table for persistent LLM configuration
-- Date: 2025-11-26

-- Create user_settings table
CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) DEFAULT 'default_user',
    
    -- LLM Configuration
    llm_provider VARCHAR(50),  -- 'openai', 'anthropic', 'google'
    llm_model VARCHAR(100),    -- e.g., 'gpt-4', 'claude-3-opus-20240229'
    
    -- API Keys (stored as JSON for multiple providers)
    api_keys JSONB DEFAULT '{}',  -- {"openai": "sk-...", "anthropic": "sk-ant-...", "google": "AIza..."}
    
    -- Last used model in chat
    last_chat_model VARCHAR(100),
    last_chat_provider VARCHAR(50),
    
    -- Preferences
    default_temperature FLOAT DEFAULT 0.7,
    default_max_tokens INTEGER DEFAULT 2000,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure one settings record per user
    UNIQUE(user_id)
);

-- Create index on user_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);

-- Insert default settings for default user
INSERT INTO user_settings (user_id, llm_provider, llm_model, last_chat_model, last_chat_provider)
VALUES ('default_user', 'openai', 'gpt-4o', 'gpt-4o', 'openai')
ON CONFLICT (user_id) DO NOTHING;

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_user_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_settings_updated_at
BEFORE UPDATE ON user_settings
FOR EACH ROW
EXECUTE FUNCTION update_user_settings_updated_at();

COMMENT ON TABLE user_settings IS 'Stores user LLM configuration and API keys persistently';
COMMENT ON COLUMN user_settings.api_keys IS 'Encrypted JSON object with API keys for different providers';
