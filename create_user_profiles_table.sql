-- Create user_profiles table for AutoWave
-- Run this SQL in your Supabase SQL Editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create user_profiles table (extends Supabase auth.users)
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

-- Enable Row Level Security
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Create policies for user_profiles
CREATE POLICY "Users can view own profile" ON public.user_profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.user_profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON public.user_profiles
    FOR INSERT WITH CHECK (auth.uid() = id);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON public.user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_subscription_tier ON public.user_profiles(subscription_tier);

-- Insert a test user profile (optional - you can remove this)
-- This creates a profile for the user ID that's been appearing in your logs
INSERT INTO public.user_profiles (id, email, full_name, subscription_tier)
VALUES (
    '746f9f78-9355-4b9a-a07d-91ba194fd2ef',
    'test@autowave.pro',
    'Test User',
    'free'
) ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    full_name = EXCLUDED.full_name,
    subscription_tier = EXCLUDED.subscription_tier,
    updated_at = NOW();

-- Verify the table was created
SELECT 'user_profiles table created successfully' as status;
SELECT * FROM public.user_profiles LIMIT 5;
