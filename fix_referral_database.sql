-- Fix AutoWave Referral Database - Remove Real Names & Use Generic Partners
-- Run this SQL in your Supabase SQL Editor to fix the database

-- 1. Delete existing sample data with real names
DELETE FROM public.referral_conversions;
DELETE FROM public.referral_visits;
DELETE FROM public.user_referrals;
DELETE FROM public.influencers;

-- 2. Insert generic partner data instead
INSERT INTO public.influencers (
    id, name, email, utm_source, referral_code, 
    discount_percentage, bonus_credits, commission_rate, is_active
) VALUES 
(
    'partner-001',
    'Tech Partner A',
    'partner-a@autowave.pro',
    'TechPartnerA',
    'TECH20',
    20.00,
    100,
    10.00,
    true
),
(
    'partner-002',
    'AI Partner B',
    'partner-b@autowave.pro',
    'AIPartnerB',
    'AI15',
    15.00,
    50,
    8.00,
    true
),
(
    'partner-003',
    'Premium Partner C',
    'partner-c@autowave.pro',
    'PremiumPartnerC',
    'PREMIUM30',
    30.00,
    150,
    12.00,
    true
);

-- 3. Verification - Check the updated data
SELECT 
    id,
    name,
    utm_source,
    referral_code,
    discount_percentage,
    bonus_credits,
    commission_rate,
    is_active
FROM public.influencers
ORDER BY id;
