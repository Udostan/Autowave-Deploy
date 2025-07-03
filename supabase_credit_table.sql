-- AutoWave Credit Usage Tracking Table
-- Create this table in your Supabase database

-- Create credit_usage table
CREATE TABLE IF NOT EXISTS public.credit_usage (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    credits_consumed INTEGER NOT NULL DEFAULT 0,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    date DATE DEFAULT CURRENT_DATE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_credit_usage_user_id ON public.credit_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_usage_date ON public.credit_usage(date);
CREATE INDEX IF NOT EXISTS idx_credit_usage_user_date ON public.credit_usage(user_id, date);
CREATE INDEX IF NOT EXISTS idx_credit_usage_task_type ON public.credit_usage(task_type);

-- Create user_credits table for tracking user credit balances
CREATE TABLE IF NOT EXISTS public.user_credits (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    plan_type TEXT DEFAULT 'free',
    total_credits INTEGER DEFAULT 50,
    used_credits INTEGER DEFAULT 0,
    remaining_credits INTEGER DEFAULT 50,
    reset_date TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '1 day'),
    last_reset TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for user_credits
CREATE INDEX IF NOT EXISTS idx_user_credits_user_id ON public.user_credits(user_id);
CREATE INDEX IF NOT EXISTS idx_user_credits_plan_type ON public.user_credits(plan_type);

-- Create function to update remaining credits
CREATE OR REPLACE FUNCTION update_user_credits()
RETURNS TRIGGER AS $$
BEGIN
    -- Update remaining credits when credit usage is inserted
    INSERT INTO public.user_credits (user_id, used_credits, remaining_credits)
    VALUES (NEW.user_id, NEW.credits_consumed, 50 - NEW.credits_consumed)
    ON CONFLICT (user_id) 
    DO UPDATE SET 
        used_credits = user_credits.used_credits + NEW.credits_consumed,
        remaining_credits = GREATEST(0, user_credits.total_credits - (user_credits.used_credits + NEW.credits_consumed)),
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update user credits
CREATE TRIGGER trigger_update_user_credits
    AFTER INSERT ON public.credit_usage
    FOR EACH ROW
    EXECUTE FUNCTION update_user_credits();

-- Enable Row Level Security (RLS)
ALTER TABLE public.credit_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_credits ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for credit_usage
CREATE POLICY "Users can view their own credit usage" ON public.credit_usage
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Service role can manage all credit usage" ON public.credit_usage
    FOR ALL USING (auth.role() = 'service_role');

-- Create RLS policies for user_credits
CREATE POLICY "Users can view their own credits" ON public.user_credits
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Service role can manage all user credits" ON public.user_credits
    FOR ALL USING (auth.role() = 'service_role');

-- Insert sample data for testing (optional)
-- INSERT INTO public.user_credits (user_id, plan_type, total_credits, remaining_credits)
-- VALUES ('test-user-123', 'free', 50, 50);

-- Grant permissions
GRANT ALL ON public.credit_usage TO service_role;
GRANT ALL ON public.user_credits TO service_role;
GRANT SELECT ON public.credit_usage TO anon;
GRANT SELECT ON public.user_credits TO anon;

-- Create view for daily credit usage summary
CREATE OR REPLACE VIEW public.daily_credit_usage AS
SELECT 
    user_id,
    date,
    SUM(credits_consumed) as total_credits_used,
    COUNT(*) as total_tasks,
    array_agg(DISTINCT task_type) as task_types_used
FROM public.credit_usage
GROUP BY user_id, date
ORDER BY date DESC;

-- Grant access to the view
GRANT SELECT ON public.daily_credit_usage TO service_role;
GRANT SELECT ON public.daily_credit_usage TO anon;

COMMENT ON TABLE public.credit_usage IS 'Tracks individual credit consumption events for each user task';
COMMENT ON TABLE public.user_credits IS 'Tracks user credit balances and plan information';
COMMENT ON VIEW public.daily_credit_usage IS 'Daily summary of credit usage per user';
