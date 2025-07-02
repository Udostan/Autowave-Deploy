# 🎯 AutoWave Influencer Referral System Guide

## 📊 Current Referral Configuration

### 💰 Customer Benefits
| Influencer | Referral Code | Discount | Bonus Credits | Commission Rate |
|------------|---------------|----------|---------------|-----------------|
| Matthew Berman | `MATTHEW20` | 20% | 100 credits | 10% |
| AI Explained | `AIEXPLAINED15` | 15% | 50 credits | 8% |
| Lex Fridman | `LEX30` | 30% | 150 credits | 12% |

### 💸 Revenue Sharing
- **Matthew Berman**: Earns 10% commission on each sale
- **AI Explained**: Earns 8% commission on each sale  
- **Lex Fridman**: Earns 12% commission on each sale

## 🔗 How to Generate Referral Links

### Method 1: UTM Parameter Links (Recommended)
```
Base URL: https://autowave.pro/

Matthew Berman:
https://autowave.pro/?utm_source=MatthewBerman&utm_medium=Youtube&utm_campaign=influence

AI Explained:
https://autowave.pro/?utm_source=AIExplained&utm_medium=Twitter&utm_campaign=promo

Lex Fridman:
https://autowave.pro/?utm_source=LexFridman&utm_medium=Podcast&utm_campaign=interview
```

### Method 2: Custom Referral Codes
Users manually enter these codes on the pricing page:
- `MATTHEW20` - 20% off + 100 bonus credits
- `AIEXPLAINED15` - 15% off + 50 bonus credits
- `LEX30` - 30% off + 150 bonus credits

## 🛠 For Admins: Adding New Influencers

### Step 1: Add to Database (Supabase)
```sql
INSERT INTO influencers (
    id, name, email, utm_source, referral_code, 
    discount_percentage, bonus_credits, commission_rate, is_active
) VALUES (
    'new-influencer-id',
    'Influencer Name',
    'email@example.com',
    'InfluencerUTM',
    'NEWCODE25',
    25.0,
    200,
    15.0,
    true
);
```

### Step 2: Update Fallback Data (for testing)
Edit `app/services/referral_service.py`:
```python
fallback_influencers = {
    'NewInfluencer': InfluencerProfile(
        id='new-influencer-id',
        name='Influencer Name',
        email='email@example.com',
        utm_source='NewInfluencer',
        referral_code='NEWCODE25',
        discount_percentage=25.0,
        bonus_credits=200,
        commission_rate=15.0,
        is_active=True
    )
}
```

## 📈 Analytics & Tracking

### Available Metrics
- **Total Visits**: UTM click tracking
- **Conversion Rate**: Visits → Purchases
- **Total Revenue**: Sum of all referral sales
- **Commission Earned**: Revenue × Commission Rate
- **Bonus Credits Given**: Total credits awarded

### API Endpoints
```
GET /referral/track?utm_source=MatthewBerman&utm_medium=Youtube
POST /referral/apply-code {"referral_code": "MATTHEW20"}
GET /referral/analytics/{influencer_id}
```

## 🎨 Frontend Integration

### Automatic UTM Detection
The system automatically detects UTM parameters when users visit:
```javascript
// Automatically applied on page load
https://autowave.pro/?utm_source=MatthewBerman
```

### Manual Code Entry
Users can enter referral codes on the pricing page:
- Real-time validation with 500ms debounce
- Visual feedback with success/error messages
- Automatic discount calculation and display

## 🚀 Deployment Status

✅ **Committed Changes:**
- Comprehensive referral system implementation
- Updated pricing ($15 Plus / $169 Pro)
- Apple Pay integration fixes
- UI updates (removed coupon system, added referral system)

✅ **Ready for Production:**
- Database schema provided
- Fallback mode for testing
- Real-time validation
- Analytics tracking
- Commission calculations

## 📋 Next Steps

1. **Deploy to Heroku** (automatic from GitHub)
2. **Create Supabase tables** using provided SQL scripts
3. **Add influencer data** to database
4. **Test referral tracking** on live site
5. **Monitor analytics** and payouts

## 🔧 Technical Details

### Database Tables
- `influencers`: Influencer profiles and settings
- `referral_visits`: UTM click tracking
- `referral_conversions`: Purchase tracking
- `user_referrals`: User-to-influencer mapping

### Session Storage
- Referral data stored in user session
- Persistent across page navigation
- Applied automatically at checkout

### Payment Integration
- Automatic discount calculation
- Bonus credits added to user account
- Commission tracking for payouts
