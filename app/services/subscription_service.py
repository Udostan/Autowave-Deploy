"""
AutoWave Subscription Management Service
Handles subscription lifecycle, credit management, and feature access control
"""

import os
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
import json

logger = logging.getLogger(__name__)

@dataclass
class SubscriptionPlan:
    """Subscription plan data structure"""
    id: str
    plan_name: str
    display_name: str
    monthly_price_usd: float
    annual_price_usd: float
    monthly_credits: int
    features: Dict[str, Any]
    is_active: bool

@dataclass
class UserSubscription:
    """User subscription data structure"""
    id: str
    user_id: str
    plan_id: str
    status: str
    payment_gateway: str
    gateway_subscription_id: Optional[str]
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool

@dataclass
class UserCredits:
    """User credits data structure"""
    user_id: str
    total_credits: int
    used_credits: int
    remaining_credits: int
    billing_period_start: datetime
    billing_period_end: datetime
    rollover_credits: int

class SubscriptionService:
    """Manages user subscriptions, credits, and feature access"""

    def __init__(self):
        self.use_supabase = False  # Will be set to True if Supabase initializes successfully
        self.supabase = None
        self.sqlite_db_path = None

        # Try to initialize Supabase first
        logger.info(f"SUPABASE_AVAILABLE: {SUPABASE_AVAILABLE}")
        if SUPABASE_AVAILABLE:
            supabase_url = os.getenv('SUPABASE_URL')
            # Use service role key for administrative operations like creating subscriptions
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')

            logger.info(f"Supabase URL: {supabase_url[:50] if supabase_url else 'None'}...")
            logger.info(f"Supabase Key: {'SET' if supabase_key else 'NOT_SET'}")
            if supabase_key:
                logger.info(f"Key type: {'SERVICE_ROLE' if supabase_key.startswith('eyJhbGciOiJIUzI1NiIs') else 'ANON' if supabase_key.startswith('eyJhbGciOiJIUzI1NiIs') else 'UNKNOWN'}")
                logger.info(f"Key first 30 chars: {supabase_key[:30]}")

            if (supabase_url and supabase_key and
                not supabase_url.startswith('your_') and
                not supabase_key.startswith('your_')):
                try:
                    logger.info("Attempting to create Supabase client...")
                    self.supabase = create_client(supabase_url, supabase_key)
                    self.use_supabase = True
                    logger.info("✅ Using Supabase for subscription management")
                except Exception as e:
                    logger.error(f"❌ Failed to initialize Supabase: {e}")
            else:
                logger.warning("❌ Supabase credentials not properly configured")
                logger.warning(f"URL check: {supabase_url is not None} and not starts with 'your_': {not supabase_url.startswith('your_') if supabase_url else 'NO_URL'}")
                logger.warning(f"Key check: {supabase_key is not None} and not starts with 'your_': {not supabase_key.startswith('your_') if supabase_key else 'NO_KEY'}")
                if supabase_key:
                    logger.warning(f"Key first 20 chars: {supabase_key[:20]}")
                if supabase_url:
                    logger.warning(f"URL first 50 chars: {supabase_url[:50]}")
        else:
            logger.warning("❌ Supabase module not available")

        # Fallback to SQLite
        if not self.use_supabase:
            self.sqlite_db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'subscriptions.db')
            logger.info("Using SQLite for subscription management (fallback mode)")
        
    def get_subscription_plans(self) -> List[SubscriptionPlan]:
        """Get all active subscription plans"""
        try:
            if self.use_supabase:
                response = self.supabase.table('subscription_plans').select('*').eq('is_active', True).execute()
                plan_data_list = response.data
            else:
                # Use SQLite fallback
                conn = sqlite3.connect(self.sqlite_db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM subscription_plans WHERE is_active = 1")
                rows = cursor.fetchall()
                conn.close()

                # Convert to dict format
                plan_data_list = []
                for row in rows:
                    plan_data_list.append({
                        'id': row[0],
                        'plan_name': row[1],
                        'display_name': row[2],
                        'monthly_price_usd': row[3],
                        'annual_price_usd': row[4],
                        'monthly_credits': row[5],
                        'features': json.loads(row[6]) if row[6] else {},
                        'is_active': bool(row[7])
                    })

            plans = []
            for plan_data in plan_data_list:
                plans.append(SubscriptionPlan(
                    id=plan_data['id'],
                    plan_name=plan_data['plan_name'],
                    display_name=plan_data['display_name'],
                    monthly_price_usd=float(plan_data['monthly_price_usd']),
                    annual_price_usd=float(plan_data['annual_price_usd']),
                    monthly_credits=plan_data['monthly_credits'],
                    features=plan_data['features'],
                    is_active=plan_data['is_active']
                ))

            return plans

        except Exception as e:
            logger.error(f"Error fetching subscription plans: {str(e)}")
            return []
    
    def get_user_subscription(self, user_id: str) -> Optional[UserSubscription]:
        """Get user's current subscription"""
        try:
            response = self.supabase.table('user_subscriptions').select('*').eq('user_id', user_id).eq('status', 'active').single().execute()
            
            if response.data:
                data = response.data
                return UserSubscription(
                    id=data['id'],
                    user_id=data['user_id'],
                    plan_id=data['plan_id'],
                    status=data['status'],
                    payment_gateway=data['payment_gateway'],
                    gateway_subscription_id=data.get('gateway_subscription_id'),
                    current_period_start=datetime.fromisoformat(data['current_period_start'].replace('Z', '+00:00')),
                    current_period_end=datetime.fromisoformat(data['current_period_end'].replace('Z', '+00:00')),
                    cancel_at_period_end=data['cancel_at_period_end']
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching user subscription: {str(e)}")
            return None
    
    def get_user_credits(self, user_id: str) -> Optional[UserCredits]:
        """Get user's current credit balance"""
        try:
            # Get current billing period
            now = datetime.utcnow()
            response = self.supabase.table('user_credits').select('*').eq('user_id', user_id).lte('billing_period_start', now.isoformat()).gte('billing_period_end', now.isoformat()).single().execute()
            
            if response.data:
                data = response.data
                return UserCredits(
                    user_id=data['user_id'],
                    total_credits=data['total_credits'],
                    used_credits=data['used_credits'],
                    remaining_credits=data['remaining_credits'],
                    billing_period_start=datetime.fromisoformat(data['billing_period_start'].replace('Z', '+00:00')),
                    billing_period_end=datetime.fromisoformat(data['billing_period_end'].replace('Z', '+00:00')),
                    rollover_credits=data['rollover_credits']
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching user credits: {str(e)}")
            return None
    
    def create_free_subscription(self, user_id: str) -> bool:
        """Create a free subscription for new users"""
        try:
            # Get free plan
            free_plan = self.supabase.table('subscription_plans').select('*').eq('plan_name', 'free').single().execute()
            
            if not free_plan.data:
                logger.error("Free plan not found")
                return False
            
            plan_id = free_plan.data['id']
            now = datetime.utcnow()
            period_end = now + timedelta(days=30)  # Monthly billing
            
            # Create subscription
            subscription_data = {
                'user_id': user_id,
                'plan_id': plan_id,
                'status': 'active',
                'payment_gateway': 'none',
                'current_period_start': now.isoformat(),
                'current_period_end': period_end.isoformat(),
                'cancel_at_period_end': False
            }
            
            self.supabase.table('user_subscriptions').insert(subscription_data).execute()
            
            # Allocate initial credits
            credits_data = {
                'user_id': user_id,
                'total_credits': free_plan.data['monthly_credits'],
                'used_credits': 0,
                'billing_period_start': now.isoformat(),
                'billing_period_end': period_end.isoformat(),
                'rollover_credits': 0
            }
            
            self.supabase.table('user_credits').insert(credits_data).execute()
            
            logger.info(f"Created free subscription for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating free subscription: {str(e)}")
            return False
    
    def consume_credits(self, user_id: str, credits: int, agent_type: str, action_type: str, description: str = "") -> bool:
        """Consume user credits for an action"""
        try:
            # Get current credits
            user_credits = self.get_user_credits(user_id)
            
            if not user_credits:
                logger.warning(f"No credits found for user {user_id}")
                return False
            
            if user_credits.remaining_credits < credits:
                logger.warning(f"Insufficient credits for user {user_id}. Required: {credits}, Available: {user_credits.remaining_credits}")
                return False
            
            # Record credit usage
            usage_data = {
                'user_id': user_id,
                'agent_type': agent_type,
                'action_type': action_type,
                'credits_consumed': credits,
                'description': description
            }
            
            self.supabase.table('credit_usage').insert(usage_data).execute()
            
            # Update used credits
            new_used_credits = user_credits.used_credits + credits
            self.supabase.table('user_credits').update({
                'used_credits': new_used_credits,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('user_id', user_id).eq('billing_period_start', user_credits.billing_period_start.isoformat()).execute()
            
            logger.info(f"Consumed {credits} credits for user {user_id}. Remaining: {user_credits.remaining_credits - credits}")
            return True
            
        except Exception as e:
            logger.error(f"Error consuming credits: {str(e)}")
            return False
    
    def check_feature_access(self, user_id: str, feature_name: str) -> Dict[str, Any]:
        """Check if user has access to a feature and usage limits"""
        try:
            # Get user subscription and plan
            subscription = self.get_user_subscription(user_id)
            if not subscription:
                return {'has_access': False, 'reason': 'No active subscription'}
            
            # Get plan features
            plan_response = self.supabase.table('subscription_plans').select('features').eq('id', subscription.plan_id).single().execute()
            
            if not plan_response.data:
                return {'has_access': False, 'reason': 'Plan not found'}
            
            features = plan_response.data['features']
            
            # Check if feature is included in plan
            if feature_name not in features:
                return {'has_access': False, 'reason': 'Feature not included in plan'}
            
            feature_config = features[feature_name]
            
            # For unlimited features (-1)
            if feature_config == -1 or feature_config is True:
                return {'has_access': True, 'unlimited': True}
            
            # For limited features, check usage
            if isinstance(feature_config, int) and feature_config > 0:
                # Get current usage
                today = datetime.utcnow().date()
                usage_response = self.supabase.table('feature_usage').select('usage_count').eq('user_id', user_id).eq('feature_name', feature_name).gte('reset_date', today.isoformat()).execute()
                
                current_usage = usage_response.data[0]['usage_count'] if usage_response.data else 0
                
                return {
                    'has_access': current_usage < feature_config,
                    'limit': feature_config,
                    'used': current_usage,
                    'remaining': max(0, feature_config - current_usage)
                }
            
            return {'has_access': True}
            
        except Exception as e:
            logger.error(f"Error checking feature access: {str(e)}")
            return {'has_access': False, 'reason': 'Error checking access'}
    
    def record_feature_usage(self, user_id: str, feature_name: str) -> bool:
        """Record usage of a limited feature"""
        try:
            today = datetime.utcnow().date()
            tomorrow = today + timedelta(days=1)
            
            # Upsert feature usage
            usage_data = {
                'user_id': user_id,
                'feature_name': feature_name,
                'usage_count': 1,
                'reset_date': tomorrow.isoformat(),
                'last_used': datetime.utcnow().isoformat()
            }
            
            # Try to update existing record
            existing = self.supabase.table('feature_usage').select('id, usage_count').eq('user_id', user_id).eq('feature_name', feature_name).gte('reset_date', today.isoformat()).execute()
            
            if existing.data:
                # Update existing record
                new_count = existing.data[0]['usage_count'] + 1
                self.supabase.table('feature_usage').update({
                    'usage_count': new_count,
                    'last_used': datetime.utcnow().isoformat()
                }).eq('id', existing.data[0]['id']).execute()
            else:
                # Insert new record
                self.supabase.table('feature_usage').insert(usage_data).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording feature usage: {str(e)}")
            return False
