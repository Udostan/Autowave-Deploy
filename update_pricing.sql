-- Update AutoWave Subscription Pricing
-- Run this in your Supabase SQL Editor to update the pricing

-- Update Plus Plan to $15/month
UPDATE public.subscription_plans 
SET 
    monthly_price_usd = 15,
    annual_price_usd = 180,  -- 15 * 12 = 180
    updated_at = NOW()
WHERE plan_name = 'plus';

-- Update Pro Plan to $169/month  
UPDATE public.subscription_plans 
SET 
    monthly_price_usd = 169,
    annual_price_usd = 2028,  -- 169 * 12 = 2028
    updated_at = NOW()
WHERE plan_name = 'pro';

-- Verify the updated pricing
SELECT plan_name, display_name, monthly_price_usd, annual_price_usd 
FROM public.subscription_plans 
ORDER BY monthly_price_usd;
