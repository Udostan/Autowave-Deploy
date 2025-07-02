-- AutoWave Subscription & Payment Management Schema
-- Extends existing Supabase schema for paywall functionality

-- 1. Subscription Plans Table
CREATE TABLE IF NOT EXISTS public.subscription_plans (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    plan_name TEXT NOT NULL UNIQUE, -- 'free', 'plus', 'pro', 'enterprise'
    display_name TEXT NOT NULL, -- 'Free Plan', 'Plus Plan', etc.
    monthly_price_usd DECIMAL(10,2) NOT NULL DEFAULT 0,
    annual_price_usd DECIMAL(10,2) NOT NULL DEFAULT 0,
    monthly_credits INTEGER NOT NULL DEFAULT 0,
    features JSONB NOT NULL DEFAULT '{}', -- Feature flags and limits
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. User Subscriptions Table
CREATE TABLE IF NOT EXISTS public.user_subscriptions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    plan_id UUID REFERENCES public.subscription_plans(id),
    status TEXT NOT NULL DEFAULT 'active', -- 'active', 'cancelled', 'expired', 'past_due'
    payment_gateway TEXT NOT NULL, -- 'paystack', 'stripe'
    gateway_subscription_id TEXT, -- External subscription ID
    gateway_customer_id TEXT, -- External customer ID
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    cancel_at_period_end BOOLEAN DEFAULT false,
    trial_start TIMESTAMP WITH TIME ZONE,
    trial_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id) -- One active subscription per user
);

-- 3. Credit Management Table
CREATE TABLE IF NOT EXISTS public.user_credits (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    total_credits INTEGER NOT NULL DEFAULT 0,
    used_credits INTEGER NOT NULL DEFAULT 0,
    remaining_credits INTEGER GENERATED ALWAYS AS (total_credits - used_credits) STORED,
    billing_period_start TIMESTAMP WITH TIME ZONE,
    billing_period_end TIMESTAMP WITH TIME ZONE,
    rollover_credits INTEGER DEFAULT 0, -- Credits from previous month
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, billing_period_start) -- One record per billing period
);

-- 4. Credit Usage Tracking
CREATE TABLE IF NOT EXISTS public.credit_usage (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    agent_type TEXT NOT NULL, -- 'prime_agent', 'code_wave', 'agent_wave', etc.
    action_type TEXT NOT NULL, -- 'chat_message', 'tool_usage', 'document_generation'
    credits_consumed INTEGER NOT NULL DEFAULT 1,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Payment Transactions Table
CREATE TABLE IF NOT EXISTS public.payment_transactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES public.user_subscriptions(id),
    payment_gateway TEXT NOT NULL,
    gateway_transaction_id TEXT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    status TEXT NOT NULL, -- 'pending', 'completed', 'failed', 'refunded'
    payment_method TEXT, -- 'card', 'bank_transfer', etc.
    gateway_response JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Feature Access Tracking
CREATE TABLE IF NOT EXISTS public.feature_usage (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    feature_name TEXT NOT NULL, -- 'code_wave_trial', 'agent_wave_trial', 'file_upload'
    usage_count INTEGER DEFAULT 0,
    daily_limit INTEGER,
    monthly_limit INTEGER,
    last_used TIMESTAMP WITH TIME ZONE,
    reset_date TIMESTAMP WITH TIME ZONE, -- When limits reset
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, feature_name, reset_date)
);

-- Insert default subscription plans (optimized pricing)
INSERT INTO public.subscription_plans (plan_name, display_name, monthly_price_usd, annual_price_usd, monthly_credits, features) VALUES
('free', 'Free Plan', 0, 0, 50, '{
    "ai_agents": ["prime_agent", "autowave_chat", "code_wave"],
    "daily_credits": 50,
    "credit_type": "daily",
    "file_upload_limit": 5,
    "support_level": "community"
}'),
('plus', 'Plus Plan', 15, 171, 8000, '{
    "ai_agents": ["prime_agent", "autowave_chat", "code_wave", "agent_wave", "research_lab"],
    "monthly_credits": 8000,
    "credit_type": "monthly",
    "prime_agent_tools": 12,
    "file_upload_limit": 100,
    "credit_rollover": true,
    "rollover_limit": 0.5,
    "support_level": "email"
}'),
('pro', 'Pro Plan', 99, 1188, 200000, '{
    "ai_agents": ["prime_agent", "autowave_chat", "code_wave", "agent_wave", "research_lab"],
    "monthly_credits": 200000,
    "credit_type": "monthly",
    "prime_agent_tools": -1,
    "file_upload_limit": -1,
    "credit_rollover": true,
    "rollover_limit": 0.3,
    "real_time_browsing": true,
    "support_level": "priority"
}'),
('enterprise', 'Enterprise', 0, 0, -1, '{
    "ai_agents": ["prime_agent", "autowave_chat", "code_wave", "agent_wave", "research_lab"],
    "prime_agent_tools": -1,
    "file_upload_limit": -1,
    "real_time_browsing": true,
    "custom_integrations": true,
    "white_label": true,
    "support_level": "dedicated"
}')
ON CONFLICT (plan_name) DO NOTHING;

-- Enable RLS
ALTER TABLE public.subscription_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_credits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.credit_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payment_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.feature_usage ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Anyone can view subscription plans" ON public.subscription_plans FOR SELECT USING (true);

CREATE POLICY "Users can view own subscription" ON public.user_subscriptions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own subscription" ON public.user_subscriptions FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own subscription" ON public.user_subscriptions FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own credits" ON public.user_credits FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own credits" ON public.user_credits FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own credits" ON public.user_credits FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own credit usage" ON public.credit_usage FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own credit usage" ON public.credit_usage FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own transactions" ON public.payment_transactions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own transactions" ON public.payment_transactions FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own feature usage" ON public.feature_usage FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own feature usage" ON public.feature_usage FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own feature usage" ON public.feature_usage FOR UPDATE USING (auth.uid() = user_id);

-- Functions for automatic credit allocation
CREATE OR REPLACE FUNCTION public.allocate_monthly_credits()
RETURNS TRIGGER AS $$
BEGIN
    -- Allocate credits when subscription is created or renewed
    INSERT INTO public.user_credits (
        user_id, 
        total_credits, 
        billing_period_start, 
        billing_period_end
    ) VALUES (
        NEW.user_id,
        (SELECT monthly_credits FROM public.subscription_plans WHERE id = NEW.plan_id),
        NEW.current_period_start,
        NEW.current_period_end
    ) ON CONFLICT (user_id, billing_period_start) DO UPDATE SET
        total_credits = EXCLUDED.total_credits,
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to allocate credits on subscription changes
CREATE TRIGGER on_subscription_created
    AFTER INSERT OR UPDATE ON public.user_subscriptions
    FOR EACH ROW EXECUTE FUNCTION public.allocate_monthly_credits();
