-- Zeus Nexus Database Migration
-- Add missing columns for multi-LLM support

-- Add llm_model column to conversations table
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS llm_model VARCHAR(50) DEFAULT 'gpt-4';

-- Add llm_provider column to conversations table
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS llm_provider VARCHAR(50);

-- Add updated_at column to conversations table
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Add llm_model column to tasks table
ALTER TABLE tasks 
ADD COLUMN IF NOT EXISTS llm_model VARCHAR(50) DEFAULT 'gpt-4';

-- Remove UNIQUE constraint on session_id (sessions can have multiple conversations)
ALTER TABLE conversations DROP CONSTRAINT IF EXISTS conversations_session_id_key;

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_conversations_llm_model ON conversations(llm_model);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_llm_model ON tasks(llm_model);

-- Display updated schema
\d conversations
\d tasks

-- Show migration completion
SELECT 'Migration completed successfully!' as status;
