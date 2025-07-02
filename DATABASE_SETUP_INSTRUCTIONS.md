# 🗄️ AutoWave Referral Database Setup Instructions

## 🎯 Quick Setup (Choose One Method)

### Method 1: SQL Editor (Recommended)
1. **Go to Supabase Dashboard**: https://supabase.com/dashboard
2. **Select your AutoWave project**
3. **Click "SQL Editor" in the left sidebar**
4. **Copy and paste the entire content** from `create_referral_database_tables.sql`
5. **Click "Run"** to execute all commands
6. **Verify**: Check "Table Editor" to see the new tables

### Method 2: Python Script
1. **Make sure you have the service key** in your `.env` file:
   ```
   SUPABASE_SERVICE_KEY=your-service-key-here
   ```
2. **Run the setup script**:
   ```bash
   cd Agent9/agen911
   python setup_referral_database.py
   ```

## 📋 What Gets Created

### 🗂️ Database Tables
1. **`influencers`** - Influencer profiles and settings
2. **`referral_visits`** - UTM click tracking
3. **`referral_conversions`** - Purchase tracking with commissions
4. **`user_referrals`** - User-to-influencer mapping

### 👥 Sample Influencers
| Name | UTM Source | Referral Code | Discount | Commission |
|------|------------|---------------|----------|------------|
| Matthew Berman | `MatthewBerman` | `MATTHEW20` | 20% | 10% |
| AI Explained | `AIExplained` | `AIEXPLAINED15` | 15% | 8% |
| Lex Fridman | `LexFridman` | `LEX30` | 30% | 12% |

## 🔧 Environment Variables Needed

Make sure these are in your `.env` file:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
```

## ✅ Verification Steps

After running the setup:

1. **Check Tables**: Go to Supabase → Table Editor
2. **Test UTM Link**: Visit `https://autowave.pro/?utm_source=MatthewBerman`
3. **Test Referral Code**: Enter `MATTHEW20` on pricing page
4. **Check Analytics**: Look for data in `referral_visits` table

## 🚨 Troubleshooting

### "Permission Denied" Error
- Make sure you're using the **service key**, not the anon key
- Check that RLS policies are set correctly

### "Table Already Exists" Error
- This is normal if you've run the setup before
- The script uses `CREATE TABLE IF NOT EXISTS`

### "Connection Failed" Error
- Verify your `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`
- Check your internet connection

## 🎯 Testing Your Setup

### Test UTM Tracking
```bash
# Visit this URL and check referral_visits table
https://autowave.pro/?utm_source=MatthewBerman&utm_medium=Youtube&utm_campaign=test
```

### Test Referral Codes
1. Go to pricing page: `https://autowave.pro/pricing`
2. Enter referral code: `MATTHEW20`
3. Should show: "✓ 20% off + 100 bonus credits!"

### Test Analytics
```sql
-- Run in Supabase SQL Editor
SELECT 
    i.name,
    i.referral_code,
    COUNT(rv.id) as total_visits,
    COUNT(rc.id) as total_conversions,
    SUM(rc.amount) as total_revenue
FROM influencers i
LEFT JOIN referral_visits rv ON i.id = rv.influencer_id
LEFT JOIN referral_conversions rc ON i.id = rc.influencer_id
GROUP BY i.id, i.name, i.referral_code;
```

## 🔄 Adding New Influencers

### Via SQL
```sql
INSERT INTO influencers (
    id, name, email, utm_source, referral_code,
    discount_percentage, bonus_credits, commission_rate, is_active
) VALUES (
    'new-influencer',
    'New Influencer Name',
    'email@example.com',
    'NewInfluencer',
    'NEWCODE25',
    25.0,
    200,
    15.0,
    true
);
```

### Via Supabase Dashboard
1. Go to Table Editor → `influencers`
2. Click "Insert" → "Insert row"
3. Fill in the required fields
4. Click "Save"

## 📊 Monitoring & Analytics

### Key Metrics to Track
- **Conversion Rate**: Visits → Purchases
- **Revenue per Influencer**: Total sales generated
- **Commission Payouts**: Amount owed to influencers
- **Popular Codes**: Most used referral codes

### Supabase Dashboard Views
- **Table Editor**: View raw data
- **API Logs**: Monitor API calls
- **Auth**: Track user registrations from referrals

## 🎉 You're Ready!

Once the database is set up:
1. ✅ Referral links will work automatically
2. ✅ UTM tracking will be recorded
3. ✅ Discounts will apply at checkout
4. ✅ Commission tracking will be active
5. ✅ Analytics will be available

Your referral system is now fully operational! 🚀
