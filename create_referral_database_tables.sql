-- AutoWave Referral System Database Tables
-- Run these SQL commands in your Supabase SQL Editor

-- 1. Create influencers table
CREATE TABLE IF NOT EXISTS public.influencers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    utm_source TEXT UNIQUE NOT NULL,
    referral_code TEXT UNIQUE NOT NULL,
    discount_percentage DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    bonus_credits INTEGER NOT NULL DEFAULT 0,
    commission_rate DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    is_active BOOLEAN NOT NULL DEFAULT true,
    total_referrals INTEGER NOT NULL DEFAULT 0,
    total_revenue DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create referral_visits table
CREATE TABLE IF NOT EXISTS public.referral_visits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    influencer_id TEXT REFERENCES public.influencers(id),
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    utm_content TEXT,
    utm_term TEXT,
    user_id TEXT,
    ip_address INET,
    user_agent TEXT,
    referrer_url TEXT,
    landing_page TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Create referral_conversions table
CREATE TABLE IF NOT EXISTS public.referral_conversions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    influencer_id TEXT REFERENCES public.influencers(id),
    user_id TEXT NOT NULL,
    referral_code TEXT,
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    amount DECIMAL(10,2) NOT NULL,
    discount_applied DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    bonus_credits_given INTEGER NOT NULL DEFAULT 0,
    commission_earned DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    plan_name TEXT,
    billing_cycle TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Create user_referrals table
CREATE TABLE IF NOT EXISTS public.user_referrals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    influencer_id TEXT REFERENCES public.influencers(id),
    referral_code TEXT,
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    discount_percentage DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    bonus_credits INTEGER NOT NULL DEFAULT 0,
    is_converted BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Insert sample influencer data
INSERT INTO public.influencers (
    id, name, email, utm_source, referral_code, 
    discount_percentage, bonus_credits, commission_rate, is_active
) VALUES 
(
    'matthew-berman',
    'Matthew Berman',
    'matthew@matthewberman.ai',
    'MatthewBerman',
    'MATTHEW20',
    20.00,
    100,
    10.00,
    true
),
(
    'ai-explained',
    'AI Explained',
    'contact@aiexplained.com',
    'AIExplained',
    'AIEXPLAINED15',
    15.00,
    50,
    8.00,
    true
),
(
    'lex-fridman',
    'Lex Fridman',
    'lex@lexfridman.com',
    'LexFridman',
    'LEX30',
    30.00,
    150,
    12.00,
    true
);

-- 6. Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_influencers_utm_source ON public.influencers(utm_source);
CREATE INDEX IF NOT EXISTS idx_influencers_referral_code ON public.influencers(referral_code);
CREATE INDEX IF NOT EXISTS idx_referral_visits_influencer_id ON public.referral_visits(influencer_id);
CREATE INDEX IF NOT EXISTS idx_referral_visits_utm_source ON public.referral_visits(utm_source);
CREATE INDEX IF NOT EXISTS idx_referral_conversions_influencer_id ON public.referral_conversions(influencer_id);
CREATE INDEX IF NOT EXISTS idx_referral_conversions_user_id ON public.referral_conversions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_referrals_user_id ON public.user_referrals(user_id);
CREATE INDEX IF NOT EXISTS idx_user_referrals_influencer_id ON public.user_referrals(influencer_id);

-- 7. Enable Row Level Security (RLS)
ALTER TABLE public.influencers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.referral_visits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.referral_conversions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_referrals ENABLE ROW LEVEL SECURITY;

-- 8. Create RLS policies (allow service role to access all data)
CREATE POLICY "Allow service role full access" ON public.influencers
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Allow service role full access" ON public.referral_visits
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Allow service role full access" ON public.referral_conversions
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Allow service role full access" ON public.user_referrals
    FOR ALL USING (auth.role() = 'service_role');

-- 9. Create function to update influencer stats
CREATE OR REPLACE FUNCTION update_influencer_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Update total referrals and revenue for the influencer
    UPDATE public.influencers 
    SET 
        total_referrals = (
            SELECT COUNT(*) 
            FROM public.referral_conversions 
            WHERE influencer_id = NEW.influencer_id
        ),
        total_revenue = (
            SELECT COALESCE(SUM(amount), 0) 
            FROM public.referral_conversions 
            WHERE influencer_id = NEW.influencer_id
        ),
        updated_at = NOW()
    WHERE id = NEW.influencer_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 10. Create trigger to automatically update influencer stats
CREATE TRIGGER trigger_update_influencer_stats
    AFTER INSERT ON public.referral_conversions
    FOR EACH ROW
    EXECUTE FUNCTION update_influencer_stats();

-- 11. Grant necessary permissions
GRANT ALL ON public.influencers TO service_role;
GRANT ALL ON public.referral_visits TO service_role;
GRANT ALL ON public.referral_conversions TO service_role;
GRANT ALL ON public.user_referrals TO service_role;

-- Verification queries (run these to check if tables were created successfully)
-- SELECT * FROM public.influencers;
-- SELECT COUNT(*) FROM public.referral_visits;
-- SELECT COUNT(*) FROM public.referral_conversions;
-- SELECT COUNT(*) FROM public.user_referrals;
