-- Enhanced History System Database Tables
-- Run this SQL in your Supabase SQL Editor

-- 1. Create agent_sessions table
CREATE TABLE IF NOT EXISTS public.agent_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL,
    agent_type TEXT NOT NULL CHECK (agent_type IN ('autowave_chat', 'prime_agent', 'agentic_code', 'research_lab', 'context7_tools', 'agent_wave')),
    session_name TEXT,
    latest_activity_id UUID,
    is_active BOOLEAN DEFAULT true,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_interactions INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'
);

-- 2. Create user_activities table
CREATE TABLE IF NOT EXISTS public.user_activities (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL,
    session_id UUID REFERENCES public.agent_sessions(id) ON DELETE CASCADE,
    agent_type TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    file_uploads JSONB DEFAULT '[]',
    processing_time_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Add file_uploads column if it doesn't exist (for existing tables)
ALTER TABLE public.user_activities
ADD COLUMN IF NOT EXISTS file_uploads JSONB DEFAULT '[]';

-- 3. Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_activities_user_id ON public.user_activities(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activities_agent_type ON public.user_activities(agent_type);
CREATE INDEX IF NOT EXISTS idx_user_activities_created_at ON public.user_activities(created_at);
CREATE INDEX IF NOT EXISTS idx_user_activities_session_id ON public.user_activities(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_user_id ON public.agent_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_updated_at ON public.agent_sessions(updated_at);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_latest_activity ON public.agent_sessions(latest_activity_id);

-- 4. Enable Row Level Security
ALTER TABLE public.agent_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_activities ENABLE ROW LEVEL SECURITY;

-- 5. Create RLS policies for agent_sessions (allow all operations for now)
DROP POLICY IF EXISTS "Allow all operations on agent_sessions" ON public.agent_sessions;
CREATE POLICY "Allow all operations on agent_sessions" ON public.agent_sessions
    FOR ALL USING (true) WITH CHECK (true);

-- 6. Create RLS policies for user_activities (allow all operations for now)
DROP POLICY IF EXISTS "Allow all operations on user_activities" ON public.user_activities;
CREATE POLICY "Allow all operations on user_activities" ON public.user_activities
    FOR ALL USING (true) WITH CHECK (true);

-- 7. Insert some test data to verify the setup
INSERT INTO public.agent_sessions (user_id, agent_type, session_name, metadata) 
VALUES 
    ('746f9f78-9355-4b9a-a07d-91ba194fd2ef', 'autowave_chat', 'Test Chat Session', '{"test": true}'),
    ('746f9f78-9355-4b9a-a07d-91ba194fd2ef', 'agentic_code', 'Test Code Session', '{"test": true}')
ON CONFLICT DO NOTHING;

-- 8. Insert test activities
INSERT INTO public.user_activities (user_id, session_id, agent_type, activity_type, input_data, output_data, success)
SELECT 
    '746f9f78-9355-4b9a-a07d-91ba194fd2ef',
    s.id,
    s.agent_type,
    'test_activity',
    '{"message": "Test message"}',
    '{"response": "Test response"}',
    true
FROM public.agent_sessions s 
WHERE s.user_id = '746f9f78-9355-4b9a-a07d-91ba194fd2ef'
ON CONFLICT DO NOTHING;

-- Verify the setup
SELECT 'agent_sessions' as table_name, count(*) as row_count FROM public.agent_sessions
UNION ALL
SELECT 'user_activities' as table_name, count(*) as row_count FROM public.user_activities;
