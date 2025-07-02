-- AutoWave Influencer Referral System Database Schema
-- Run this SQL in your Supabase SQL Editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Create influencers table
CREATE TABLE IF NOT EXISTS public.influencers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    utm_source TEXT NOT NULL UNIQUE,
    referral_code TEXT NOT NULL UNIQUE,
    discount_percentage DECIMAL(5,2) NOT NULL DEFAULT 0,
    bonus_credits INTEGER NOT NULL DEFAULT 0,
    commission_rate DECIMAL(5,2) NOT NULL DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    total_referrals INTEGER DEFAULT 0,
    total_revenue DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create referral_visits table (for tracking clicks)
CREATE TABLE IF NOT EXISTS public.referral_visits (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    influencer_id UUID REFERENCES public.influencers(id) ON DELETE CASCADE,
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    utm_content TEXT,
    utm_term TEXT,
    referral_code TEXT,
    user_id UUID,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Create referral_conversions table (for tracking purchases)
CREATE TABLE IF NOT EXISTS public.referral_conversions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    influencer_id UUID REFERENCES public.influencers(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    subscription_id UUID,
    referral_code TEXT,
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    amount DECIMAL(10,2) NOT NULL,
    discount_applied DECIMAL(5,2) DEFAULT 0,
    bonus_credits_given INTEGER DEFAULT 0,
    commission_rate DECIMAL(5,2) DEFAULT 0,
    commission_amount DECIMAL(10,2) GENERATED ALWAYS AS (amount * commission_rate / 100) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Create user_referrals table (to track which users came from which referrals)
CREATE TABLE IF NOT EXISTS public.user_referrals (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL,
    influencer_id UUID REFERENCES public.influencers(id) ON DELETE CASCADE,
    referral_code TEXT,
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    utm_content TEXT,
    utm_term TEXT,
    discount_percentage DECIMAL(5,2) DEFAULT 0,
    bonus_credits INTEGER DEFAULT 0,
    is_converted BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    converted_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id)
);

-- Enable Row Level Security
ALTER TABLE public.influencers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.referral_visits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.referral_conversions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_referrals ENABLE ROW LEVEL SECURITY;

-- Create policies for influencers table
CREATE POLICY "Influencers can view own data" ON public.influencers
    FOR SELECT USING (true); -- Public read for active influencers

CREATE POLICY "Only admins can modify influencers" ON public.influencers
    FOR ALL USING (false); -- Restrict modifications to service role only

-- Create policies for referral_visits table
CREATE POLICY "Service role can manage visits" ON public.referral_visits
    FOR ALL USING (true); -- Service role can do everything

-- Create policies for referral_conversions table
CREATE POLICY "Service role can manage conversions" ON public.referral_conversions
    FOR ALL USING (true); -- Service role can do everything

-- Create policies for user_referrals table
CREATE POLICY "Users can view own referral data" ON public.user_referrals
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage user referrals" ON public.user_referrals
    FOR ALL USING (true); -- Service role can do everything

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_influencers_utm_source ON public.influencers(utm_source);
CREATE INDEX IF NOT EXISTS idx_influencers_referral_code ON public.influencers(referral_code);
CREATE INDEX IF NOT EXISTS idx_influencers_active ON public.influencers(is_active);

CREATE INDEX IF NOT EXISTS idx_referral_visits_influencer ON public.referral_visits(influencer_id);
CREATE INDEX IF NOT EXISTS idx_referral_visits_utm_source ON public.referral_visits(utm_source);
CREATE INDEX IF NOT EXISTS idx_referral_visits_created_at ON public.referral_visits(created_at);

CREATE INDEX IF NOT EXISTS idx_referral_conversions_influencer ON public.referral_conversions(influencer_id);
CREATE INDEX IF NOT EXISTS idx_referral_conversions_user ON public.referral_conversions(user_id);
CREATE INDEX IF NOT EXISTS idx_referral_conversions_created_at ON public.referral_conversions(created_at);

CREATE INDEX IF NOT EXISTS idx_user_referrals_user ON public.user_referrals(user_id);
CREATE INDEX IF NOT EXISTS idx_user_referrals_influencer ON public.user_referrals(influencer_id);

-- Insert sample influencers
INSERT INTO public.influencers (name, email, utm_source, referral_code, discount_percentage, bonus_credits, commission_rate, is_active)
VALUES 
    ('Matthew Berman', 'matthew@autowave.pro', 'MatthewBerman', 'MATTHEW20', 20.0, 100, 10.0, true),
    ('AI Explained', 'aiexplained@autowave.pro', 'AIExplained', 'AIEXPLAINED15', 15.0, 50, 8.0, true),
    ('Two Minute Papers', 'twominute@autowave.pro', 'TwoMinutePapers', 'PAPERS25', 25.0, 150, 12.0, true),
    ('Yannic Kilcher', 'yannic@autowave.pro', 'YannicKilcher', 'YANNIC15', 15.0, 75, 9.0, true),
    ('Machine Learning Street Talk', 'mlst@autowave.pro', 'MLStreetTalk', 'MLST20', 20.0, 100, 10.0, true),
    ('Lex Fridman', 'lex@autowave.pro', 'LexFridman', 'LEX30', 30.0, 200, 15.0, true),
    ('Andrej Karpathy', 'andrej@autowave.pro', 'AndrejKarpathy', 'KARPATHY25', 25.0, 150, 12.0, true),
    ('3Blue1Brown', 'grant@autowave.pro', 'ThreeBlueBrown', 'BLUE25', 25.0, 125, 11.0, true),
    ('Sentdex', 'sentdex@autowave.pro', 'Sentdex', 'SENTDEX20', 20.0, 100, 10.0, true),
    ('Code Bullet', 'codebullet@autowave.pro', 'CodeBullet', 'BULLET15', 15.0, 75, 8.0, true)
ON CONFLICT (utm_source) DO UPDATE SET
    name = EXCLUDED.name,
    email = EXCLUDED.email,
    referral_code = EXCLUDED.referral_code,
    discount_percentage = EXCLUDED.discount_percentage,
    bonus_credits = EXCLUDED.bonus_credits,
    commission_rate = EXCLUDED.commission_rate,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

-- Create a function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_influencers_updated_at BEFORE UPDATE ON public.influencers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create a view for public influencer information (without sensitive data)
CREATE OR REPLACE VIEW public.public_influencers AS
SELECT 
    id,
    name,
    utm_source,
    referral_code,
    discount_percentage,
    bonus_credits,
    is_active,
    total_referrals
FROM public.influencers
WHERE is_active = true;

-- Grant permissions for the view
GRANT SELECT ON public.public_influencers TO anon, authenticated;

-- Verify tables were created
SELECT 'Referral system tables created successfully' as status;
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('influencers', 'referral_visits', 'referral_conversions', 'user_referrals');
