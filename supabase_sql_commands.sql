-- AutoWave Supabase Subscription Tables
-- Run these commands in your Supabase SQL Editor

-- 1. Create subscription_plans table
CREATE TABLE IF NOT EXISTS public.subscription_plans (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    plan_name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    monthly_price_usd DECIMAL(10,2) NOT NULL DEFAULT 0,
    annual_price_usd DECIMAL(10,2) NOT NULL DEFAULT 0,
    monthly_credits INTEGER NOT NULL DEFAULT 0,
    features JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create user_subscriptions table
CREATE TABLE IF NOT EXISTS public.user_subscriptions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    plan_id UUID REFERENCES public.subscription_plans(id),
    status TEXT NOT NULL DEFAULT 'active',
    payment_gateway TEXT NOT NULL,
    gateway_subscription_id TEXT,
    gateway_customer_id TEXT,
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    cancel_at_period_end BOOLEAN DEFAULT false,
    trial_start TIMESTAMP WITH TIME ZONE,
    trial_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- 3. Insert default subscription plans
INSERT INTO public.subscription_plans (plan_name, display_name, monthly_price_usd, annual_price_usd, monthly_credits, features, is_active)
VALUES 
(
    'free',
    'Free Plan',
    0,
    0,
    50,
    '{"ai_agents": ["prime_agent", "autowave_chat", "code_wave"], "daily_credits": 50, "credit_type": "daily", "file_upload_limit": 5, "support_level": "community"}',
    true
),
(
    'plus',
    'Plus Plan',
    29,
    348,
    8000,
    '{"ai_agents": ["prime_agent", "autowave_chat", "code_wave", "agent_wave", "research_lab"], "monthly_credits": 8000, "credit_type": "monthly", "prime_agent_tools": 12, "file_upload_limit": 100, "credit_rollover": true, "rollover_limit": 0.5, "support_level": "email"}',
    true
),
(
    'pro',
    'Pro Plan',
    99,
    1188,
    200000,
    '{"ai_agents": ["prime_agent", "autowave_chat", "code_wave", "agent_wave", "research_lab"], "monthly_credits": 200000, "credit_type": "monthly", "prime_agent_tools": -1, "file_upload_limit": -1, "credit_rollover": true, "rollover_limit": 0.3, "real_time_browsing": true, "support_level": "priority"}',
    true
)
ON CONFLICT (plan_name) DO NOTHING;

-- 4. Create credit management table (optional)
CREATE TABLE IF NOT EXISTS public.user_credits (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    total_credits INTEGER NOT NULL DEFAULT 0,
    used_credits INTEGER NOT NULL DEFAULT 0,
    remaining_credits INTEGER GENERATED ALWAYS AS (total_credits - used_credits) STORED,
    billing_period_start TIMESTAMP WITH TIME ZONE,
    billing_period_end TIMESTAMP WITH TIME ZONE,
    rollover_credits INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, billing_period_start)
);

-- 5. Create payment transactions table (optional)
CREATE TABLE IF NOT EXISTS public.payment_transactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES public.user_subscriptions(id),
    payment_gateway TEXT NOT NULL,
    gateway_transaction_id TEXT NOT NULL,
    amount_usd DECIMAL(10,2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    status TEXT NOT NULL,
    payment_method TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Enable Row Level Security (RLS) for security
ALTER TABLE public.subscription_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_credits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payment_transactions ENABLE ROW LEVEL SECURITY;

-- 7. Create RLS policies
-- Allow everyone to read subscription plans
CREATE POLICY "Allow public read access to subscription plans" ON public.subscription_plans
    FOR SELECT USING (true);

-- Allow users to read their own subscriptions
CREATE POLICY "Users can view their own subscriptions" ON public.user_subscriptions
    FOR SELECT USING (auth.uid() = user_id);

-- Allow users to read their own credits
CREATE POLICY "Users can view their own credits" ON public.user_credits
    FOR SELECT USING (auth.uid() = user_id);

-- Allow users to read their own transactions
CREATE POLICY "Users can view their own transactions" ON public.payment_transactions
    FOR SELECT USING (auth.uid() = user_id);

-- Allow service role to manage all data (for backend operations)
CREATE POLICY "Service role can manage subscription plans" ON public.subscription_plans
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role can manage user subscriptions" ON public.user_subscriptions
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role can manage user credits" ON public.user_credits
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role can manage transactions" ON public.payment_transactions
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');
