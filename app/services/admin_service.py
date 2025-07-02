"""
AutoWave Admin Service
Manages admin users and special access privileges
"""

import os
import logging
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

logger = logging.getLogger(__name__)

class AdminService:
    """Manages admin users and special privileges"""

    def __init__(self):
        self.use_supabase = False
        self.supabase = None
        self.sqlite_db_path = None

        # Try to initialize Supabase first
        if SUPABASE_AVAILABLE:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')

            if (supabase_url and supabase_key and
                not supabase_url.startswith('your_') and
                not supabase_key.startswith('your_')):
                try:
                    self.supabase = create_client(supabase_url, supabase_key)
                    self.use_supabase = True
                    logger.info("Using Supabase for admin management")
                except Exception as e:
                    logger.warning(f"Failed to initialize Supabase: {e}")

        # Fallback to SQLite
        if not self.use_supabase:
            self.sqlite_db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'subscriptions.db')
            logger.info("Using SQLite for admin management (fallback mode)")

        # Admin emails with special access
        self.admin_emails = [
            'reffynestan@gmail.com',
            'autowave101@gmail.com'
        ]
    
    def is_admin(self, email: str) -> bool:
        """Check if email is an admin"""
        return email.lower() in [admin.lower() for admin in self.admin_emails]
    
    def grant_admin_access(self, user_id: str, email: str) -> bool:
        """Grant admin access to a user"""
        try:
            if not self.is_admin(email):
                logger.warning(f"Attempted to grant admin access to non-admin email: {email}")
                return False

            # If not using Supabase, just return True for admin emails (testing mode)
            if not self.use_supabase:
                logger.info(f"Admin access granted to {email} (testing mode)")
                return True

            # Create or update admin subscription (Pro plan with unlimited everything)
            admin_plan = self.get_admin_plan()
            if not admin_plan:
                logger.error("Admin plan not found")
                return False
            
            # Check if user already has a subscription
            existing_sub = self.supabase.table('user_subscriptions').select('*').eq('user_id', user_id).execute()
            
            now = datetime.utcnow()
            period_end = now + timedelta(days=365 * 10)  # 10 years for admins
            
            subscription_data = {
                'user_id': user_id,
                'plan_id': admin_plan['id'],
                'status': 'active',
                'payment_gateway': 'admin',
                'gateway_subscription_id': f'admin_{user_id}',
                'gateway_customer_id': f'admin_customer_{user_id}',
                'current_period_start': now.isoformat(),
                'current_period_end': period_end.isoformat(),
                'cancel_at_period_end': False
            }
            
            if existing_sub.data:
                # Update existing subscription
                self.supabase.table('user_subscriptions').update(subscription_data).eq('user_id', user_id).execute()
            else:
                # Create new subscription
                self.supabase.table('user_subscriptions').insert(subscription_data).execute()
            
            # Grant unlimited credits
            credits_data = {
                'user_id': user_id,
                'total_credits': -1,  # -1 means unlimited
                'used_credits': 0,
                'billing_period_start': now.isoformat(),
                'billing_period_end': period_end.isoformat(),
                'rollover_credits': 0
            }
            
            # Check if credits record exists
            existing_credits = self.supabase.table('user_credits').select('*').eq('user_id', user_id).execute()
            
            if existing_credits.data:
                # Update existing credits
                self.supabase.table('user_credits').update(credits_data).eq('user_id', user_id).execute()
            else:
                # Create new credits record
                self.supabase.table('user_credits').insert(credits_data).execute()
            
            # Update user profile to mark as admin
            self.supabase.table('user_profiles').update({
                'subscription_tier': 'admin',
                'preferences': {'is_admin': True, 'admin_granted_at': now.isoformat()},
                'updated_at': now.isoformat()
            }).eq('id', user_id).execute()
            
            logger.info(f"Granted admin access to user {user_id} ({email})")
            return True
            
        except Exception as e:
            logger.error(f"Error granting admin access: {str(e)}")
            return False
    
    def get_admin_plan(self) -> Optional[Dict[str, Any]]:
        """Get or create the admin plan"""
        try:
            # If not using Supabase, return a mock admin plan
            if not self.use_supabase:
                return {
                    'id': 'admin-plan-id',
                    'plan_name': 'admin',
                    'display_name': 'Admin Plan',
                    'monthly_price_usd': 0,
                    'annual_price_usd': 0,
                    'monthly_credits': -1,
                    'features': {
                        'ai_agents': ['prime_agent', 'autowave_chat', 'code_wave', 'agent_wave', 'research_lab'],
                        'prime_agent_tools': -1,
                        'file_upload_limit': -1,
                        'real_time_browsing': True,
                        'custom_integrations': True,
                        'white_label': True,
                        'support_level': 'admin',
                        'is_admin': True,
                        'unlimited_everything': True
                    },
                    'is_active': True
                }

            # Try to get existing admin plan
            response = self.supabase.table('subscription_plans').select('*').eq('plan_name', 'admin').execute()

            if response.data:
                return response.data[0]
            
            # Create admin plan if it doesn't exist
            admin_plan_data = {
                'plan_name': 'admin',
                'display_name': 'Admin Plan',
                'monthly_price_usd': 0,
                'annual_price_usd': 0,
                'monthly_credits': -1,  # Unlimited
                'features': {
                    'ai_agents': ['prime_agent', 'autowave_chat', 'code_wave', 'agent_wave', 'research_lab'],
                    'prime_agent_tools': -1,  # Unlimited
                    'file_upload_limit': -1,  # Unlimited
                    'real_time_browsing': True,
                    'custom_integrations': True,
                    'white_label': True,
                    'support_level': 'admin',
                    'is_admin': True,
                    'unlimited_everything': True
                },
                'is_active': True
            }
            
            response = self.supabase.table('subscription_plans').insert(admin_plan_data).execute()
            
            if response.data:
                logger.info("Created admin plan")
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting/creating admin plan: {str(e)}")
            return None
    
    def setup_admin_users(self) -> Dict[str, Any]:
        """Set up admin access for all admin emails"""
        results = {
            'success': True,
            'admins_processed': [],
            'errors': []
        }
        
        try:
            for email in self.admin_emails:
                try:
                    # Find user by email
                    user_response = self.supabase.table('user_profiles').select('*').eq('email', email).execute()
                    
                    if user_response.data:
                        user = user_response.data[0]
                        user_id = user['id']
                        
                        # Grant admin access
                        if self.grant_admin_access(user_id, email):
                            results['admins_processed'].append({
                                'email': email,
                                'user_id': user_id,
                                'status': 'granted'
                            })
                        else:
                            results['errors'].append(f"Failed to grant admin access to {email}")
                    else:
                        results['errors'].append(f"User not found for email: {email}")
                        
                except Exception as e:
                    results['errors'].append(f"Error processing {email}: {str(e)}")
            
            if results['errors']:
                results['success'] = False
            
            return results
            
        except Exception as e:
            logger.error(f"Error setting up admin users: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'admins_processed': [],
                'errors': [str(e)]
            }
    
    def check_user_admin_status(self, user_id: str) -> Dict[str, Any]:
        """Check if a user has admin status and their current access level"""
        try:
            # If not using Supabase, return mock admin status for admin emails
            if not self.use_supabase:
                # For testing, assume user_id contains email or is an admin user
                is_admin_user = user_id in ['admin-reffynestan', 'admin-autowave101'] or '@' in user_id and self.is_admin(user_id)
                return {
                    'is_admin': is_admin_user,
                    'email': user_id if '@' in user_id else 'admin@autowave.pro',
                    'subscription_tier': 'admin' if is_admin_user else 'free',
                    'has_admin_subscription': is_admin_user,
                    'has_unlimited_credits': is_admin_user,
                    'preferences': {'is_admin': is_admin_user},
                    'subscription_data': {'status': 'active', 'payment_gateway': 'admin'} if is_admin_user else None,
                    'credits_data': {'total_credits': -1, 'used_credits': 0} if is_admin_user else None
                }

            # Get user profile
            user_response = self.supabase.table('user_profiles').select('*').eq('id', user_id).execute()

            if not user_response.data:
                return {'is_admin': False, 'error': 'User not found'}

            user = user_response.data[0]
            email = user.get('email', '')
            
            # Check if email is in admin list
            is_admin_email = self.is_admin(email)
            
            # Check subscription
            subscription_response = self.supabase.table('user_subscriptions').select('*').eq('user_id', user_id).execute()
            
            # Check credits
            credits_response = self.supabase.table('user_credits').select('*').eq('user_id', user_id).execute()
            
            return {
                'is_admin': is_admin_email,
                'email': email,
                'subscription_tier': user.get('subscription_tier', 'free'),
                'has_admin_subscription': bool(subscription_response.data and subscription_response.data[0].get('payment_gateway') == 'admin'),
                'has_unlimited_credits': bool(credits_response.data and credits_response.data[0].get('total_credits') == -1),
                'preferences': user.get('preferences', {}),
                'subscription_data': subscription_response.data[0] if subscription_response.data else None,
                'credits_data': credits_response.data[0] if credits_response.data else None
            }
            
        except Exception as e:
            logger.error(f"Error checking admin status: {str(e)}")
            return {'is_admin': False, 'error': str(e)}

# Global admin service instance
admin_service = AdminService()
