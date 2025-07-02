-- AutoWave Supabase Database Schema
-- Complete schema for storing all user activities and memory integration

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. User Profiles Table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    preferences JSONB DEFAULT '{}',
    subscription_tier TEXT DEFAULT 'free',
    total_activities INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Agent Sessions Table (Enhanced for unified history tracking)
CREATE TABLE IF NOT EXISTS public.agent_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    agent_type TEXT NOT NULL CHECK (agent_type IN ('autowave_chat', 'prime_agent', 'agentic_code', 'research_lab', 'context7_tools', 'agent_wave')),
    session_name TEXT, -- Human-readable session name
    latest_activity_id UUID, -- Reference to the most recent activity in this session
    is_active BOOLEAN DEFAULT true,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_interactions INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'
);

-- 3. User Activities Table (Main activity log)
CREATE TABLE IF NOT EXISTS public.user_activities (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    session_id UUID REFERENCES public.agent_sessions(id) ON DELETE SET NULL,
    agent_type TEXT NOT NULL CHECK (agent_type IN ('autowave_chat', 'prime_agent', 'agentic_code', 'research_lab', 'context7_tools', 'agent_wave')),
    activity_type TEXT NOT NULL CHECK (activity_type IN ('chat', 'task_execution', 'code_generation', 'research', 'tool_usage', 'file_upload', 'campaign_creation')),
    input_data JSONB NOT NULL,
    output_data JSONB,
    file_uploads JSONB DEFAULT '[]',
    processing_time_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- 4. File Uploads Table
CREATE TABLE IF NOT EXISTS public.file_uploads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    activity_id UUID REFERENCES public.user_activities(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    file_content TEXT, -- For text files
    file_url TEXT, -- For stored files
    analysis_result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. AutoWave Chat Conversations
CREATE TABLE IF NOT EXISTS public.chat_conversations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    activity_id UUID REFERENCES public.user_activities(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    message_type TEXT DEFAULT 'user' CHECK (message_type IN ('user', 'assistant', 'system')),
    tokens_used INTEGER,
    model_used TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Prime Agent Tasks
CREATE TABLE IF NOT EXISTS public.prime_agent_tasks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    activity_id UUID REFERENCES public.user_activities(id) ON DELETE CASCADE,
    task_description TEXT NOT NULL,
    task_status TEXT DEFAULT 'pending' CHECK (task_status IN ('pending', 'in_progress', 'completed', 'failed')),
    use_visual_browser BOOLEAN DEFAULT false,
    steps_completed JSONB DEFAULT '[]',
    final_result TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 7. Agentic Code Projects
CREATE TABLE IF NOT EXISTS public.code_projects (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    activity_id UUID REFERENCES public.user_activities(id) ON DELETE CASCADE,
    project_name TEXT,
    description TEXT NOT NULL,
    programming_language TEXT,
    framework TEXT,
    generated_files JSONB DEFAULT '[]',
    execution_status TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. Research Lab Queries
CREATE TABLE IF NOT EXISTS public.research_queries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    activity_id UUID REFERENCES public.user_activities(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    research_questions JSONB DEFAULT '[]',
    findings JSONB DEFAULT '[]',
    final_report TEXT,
    sources_count INTEGER DEFAULT 0,
    research_depth TEXT DEFAULT 'standard' CHECK (research_depth IN ('quick', 'standard', 'deep')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 9. Context7 Tool Usage
CREATE TABLE IF NOT EXISTS public.context7_usage (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    activity_id UUID REFERENCES public.user_activities(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    tool_category TEXT,
    request_details JSONB NOT NULL,
    result_data JSONB,
    screenshots JSONB DEFAULT '[]',
    success BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 10. Agent Wave Campaigns
CREATE TABLE IF NOT EXISTS public.agent_wave_campaigns (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    activity_id UUID REFERENCES public.user_activities(id) ON DELETE CASCADE,
    campaign_type TEXT NOT NULL CHECK (campaign_type IN ('email', 'seo', 'learning_path')),
    campaign_name TEXT,
    target_audience TEXT,
    generated_content JSONB,
    performance_metrics JSONB DEFAULT '{}',
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'completed', 'archived')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 11. Memory Integration Table
CREATE TABLE IF NOT EXISTS public.memory_links (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    activity_id UUID REFERENCES public.user_activities(id) ON DELETE CASCADE,
    qdrant_collection TEXT NOT NULL,
    qdrant_point_id TEXT NOT NULL,
    memory_type TEXT NOT NULL CHECK (memory_type IN ('preference', 'pattern', 'context')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 12. User Preferences & Settings
CREATE TABLE IF NOT EXISTS public.user_preferences (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    agent_type TEXT NOT NULL CHECK (agent_type IN ('autowave_chat', 'prime_agent', 'agentic_code', 'research_lab', 'context7_tools', 'agent_wave', 'global')),
    preference_key TEXT NOT NULL,
    preference_value JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, agent_type, preference_key)
);

-- 13. Usage Analytics
CREATE TABLE IF NOT EXISTS public.usage_analytics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    agent_type TEXT NOT NULL CHECK (agent_type IN ('autowave_chat', 'prime_agent', 'agentic_code', 'research_lab', 'context7_tools', 'agent_wave')),
    activity_count INTEGER DEFAULT 0,
    total_processing_time_ms INTEGER DEFAULT 0,
    files_uploaded INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, date, agent_type)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_activities_user_id ON public.user_activities(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activities_agent_type ON public.user_activities(agent_type);
CREATE INDEX IF NOT EXISTS idx_user_activities_created_at ON public.user_activities(created_at);
CREATE INDEX IF NOT EXISTS idx_user_activities_session_id ON public.user_activities(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_user_id ON public.agent_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_updated_at ON public.agent_sessions(updated_at);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_latest_activity ON public.agent_sessions(latest_activity_id);
CREATE INDEX IF NOT EXISTS idx_file_uploads_user_id ON public.file_uploads(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_conversations_user_id ON public.chat_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_user_date ON public.usage_analytics(user_id, date);

-- Enable Row Level Security (RLS)
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.file_uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.prime_agent_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.code_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.research_queries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.context7_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_wave_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.memory_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage_analytics ENABLE ROW LEVEL SECURITY;
