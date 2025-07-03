"""
Credit Management Service for AutoWave
Handles credit consumption, tracking, and limits based on competitor analysis
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
# from .database_service import DatabaseService  # Not available, using fallback mode

logger = logging.getLogger(__name__)

class CreditService:
    """Service for managing user credits and consumption tracking"""
    
    # Credit costs based on competitor analysis (Genspark/Manus) - EXACT MATCH
    CREDIT_COSTS = {
        # Basic AI Tasks (Genspark-style)
        'chat_message': 1,
        'simple_search': 2,
        'text_generation': 2,
        'basic_query': 1,

        # AutoWave Chat (Genspark-style)
        'autowave_chat_basic': 2,
        'autowave_chat_advanced': 4,

        # Code Wave (Website Creation) - Manus-style
        'code_wave_simple': 200,      # Simple webpage (Manus: 200 credits)
        'code_wave_advanced': 360,    # Advanced webpage (Manus: 360 credits)
        'code_wave_complex': 900,     # Complex web app (Manus: 900 credits)

        # Agent Wave (Document Processing) - Genspark-style
        'agent_wave_email': 8,
        'agent_wave_seo': 12,
        'agent_wave_learning': 15,
        'agent_wave_document': 10,
        
        # Prime Agent Tools - Genspark-style pricing
        'prime_agent_basic': 5,
        'prime_agent_complex': 12,
        'prime_agent_visual_browser': 15,
        'prime_agent_multi_tool': 20,  # Multi-tool orchestration costs more
        'prime_agent_job_search': 6,
        'prime_agent_travel': 8,
        'prime_agent_real_estate': 7,
        'prime_agent_weather': 2,
        'prime_agent_news': 3,
        'prime_agent_flight': 10,
        'prime_agent_hotel': 8,

        # Research Lab - Genspark-style pricing
        'research_basic': 8,
        'research_advanced': 15,
        'research_deep_analysis': 25,
        
        # File Processing
        'file_upload_small': 5,
        'file_upload_medium': 10,
        'file_upload_large': 20,
        
        # Web Browsing
        'web_browse_page': 8,
        'web_browse_multiple': 15,
        'web_scraping': 12,

        # Context 7 Tools (Prime Agent Tools) - All 25 Tools
        'context7_ride_booking': 8,
        'context7_flight_booking': 12,
        'context7_hotel_booking': 10,
        'context7_job_search': 15,
        'context7_medical_appointment': 12,
        'context7_government_services': 10,
        'context7_package_tracking': 8,
        'context7_financial_monitoring': 12,
        'context7_form_filling': 10,
        'context7_business_plan': 20,
        'context7_travel_planning': 15,
        'context7_pharmacy_search': 10,
        'context7_car_rental': 12,
        'context7_fitness_services': 10,
        'context7_home_services': 12,
        'context7_legal_services': 15,

        # New Context 7 Tools (9 Additional Tools)
        'context7_online_course_search': 12,
        'context7_banking_services': 12,
        'context7_appliance_repair': 10,
        'context7_gardening_services': 10,
        'context7_event_planning': 15,
        'context7_auto_maintenance': 10,
        'context7_tech_support': 12,
        'context7_cleaning_services': 10,
        'context7_tutoring_services': 12
    }
    
    # Plan credit allocations (optimized for healthy profit margins)
    PLAN_CREDITS = {
        'free': {
            'type': 'daily',
            'amount': 50,  # 50 daily credits (Nigerian market preference)
            'rollover': False
        },
        'plus': {
            'type': 'monthly',
            'amount': 8000,  # 8,000 credits per month (~267/day)
            'rollover': True,
            'rollover_limit': 0.5  # 50% rollover
        },
        'pro': {
            'type': 'monthly',
            'amount': 200000,  # 200,000 credits per month (~6,667/day)
            'rollover': True,
            'rollover_limit': 0.3  # 30% rollover
        }
    }
    
    def __init__(self):
        self.db = None
        self.supabase = None

        # Try to initialize Supabase directly for credit tracking
        try:
            from supabase import create_client
            import os

            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')

            if supabase_url and supabase_key:
                self.supabase = create_client(supabase_url, supabase_key)
                self.db = True  # Mark as available
                logger.info("✅ Credit service initialized with Supabase")
            else:
                logger.warning("❌ Supabase credentials not found, using fallback mode")
        except Exception as e:
            logger.warning(f"❌ Failed to initialize Supabase for credits: {e}, using fallback mode")
    
    def get_user_credits(self, user_id: str) -> Dict[str, Any]:
        """Get user's current credit status"""
        try:
            # If Supabase available, get real credit data
            if self.supabase:
                return self._get_credits_from_supabase(user_id)

            # If no database service available, return free plan defaults with dynamic tracking
            if not self.db:
                # Get usage from fallback storage
                today_usage = self.get_daily_usage_fallback(user_id)
                remaining = max(0, 50 - today_usage)

                return {
                    'plan': 'free',
                    'type': 'daily',
                    'remaining': remaining,
                    'total': 50,
                    'reset_date': None,
                    'percentage': (remaining / 50) * 100
                }

            # Get user's current plan
            user_plan = self.db.get_user_subscription(user_id)
            plan_name = user_plan.get('plan_name', 'free') if user_plan else 'free'

            # Get plan configuration
            plan_config = self.PLAN_CREDITS.get(plan_name, self.PLAN_CREDITS['free'])

            # Get current credit usage
            if plan_config['type'] == 'daily':
                # Daily credits (Free plan only)
                today = datetime.now().date()
                if self.db:
                    usage = self.db.get_daily_credit_usage(user_id, today)
                else:
                    usage = self.get_daily_usage_fallback(user_id)
                remaining = max(0, plan_config['amount'] - usage)
                reset_date = datetime.combine(today + timedelta(days=1), datetime.min.time())
            else:
                # Monthly credits (Plus and Pro plans)
                current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                usage = self.db.get_monthly_credit_usage(user_id, current_month) if self.db else 0

                # Handle rollover credits
                total_available = plan_config['amount']
                if plan_config.get('rollover') and self.db:
                    rollover_credits = self.db.get_rollover_credits(user_id)
                    total_available += rollover_credits

                remaining = max(0, total_available - usage)
                reset_date = current_month + timedelta(days=32)
                reset_date = reset_date.replace(day=1)

            percentage = (remaining / plan_config['amount']) * 100 if plan_config['amount'] > 0 else 0

            return {
                'plan': plan_name,
                'type': plan_config['type'],
                'remaining': remaining,
                'total': plan_config['amount'],
                'reset_date': reset_date.isoformat() if reset_date else None,
                'percentage': percentage,
                'usage_today': usage if plan_config['type'] == 'daily' else None
            }

        except Exception as e:
            logger.error(f"Error getting user credits: {str(e)}")
            # Return safe defaults for free plan
            return {
                'plan': 'free',
                'type': 'daily',
                'remaining': 50,
                'total': 50,
                'reset_date': None,
                'percentage': 100
            }
    
    def consume_credits(self, user_id: str, task_type: str, amount: Optional[int] = None) -> Dict[str, Any]:
        """Consume credits for a specific task"""
        try:
            # Get credit cost for task
            credit_cost = amount if amount is not None else self.CREDIT_COSTS.get(task_type, 1)
            
            # Get user's current credits
            credit_status = self.get_user_credits(user_id)
            
            # Check if user has unlimited credits
            if credit_status['type'] == 'unlimited':
                # Log usage but don't deduct
                self.db.log_credit_usage(user_id, task_type, credit_cost, 'unlimited')
                return {
                    'success': True,
                    'credits_consumed': credit_cost,
                    'remaining_credits': -1,
                    'plan': credit_status['plan']
                }
            
            # Check if user has enough credits
            if credit_status['remaining'] < credit_cost:
                return {
                    'success': False,
                    'error': 'Insufficient credits',
                    'credits_needed': credit_cost,
                    'credits_available': credit_status['remaining'],
                    'plan': credit_status['plan']
                }
            
            # Consume credits
            if self.supabase:
                success = self._consume_credits_supabase(user_id, task_type, credit_cost)
            else:
                # Fallback mode - use in-memory storage
                success = self._consume_credits_fallback(user_id, credit_cost, task_type)

            if success:
                new_remaining = credit_status['remaining'] - credit_cost
                return {
                    'success': True,
                    'credits_consumed': credit_cost,
                    'remaining_credits': new_remaining,
                    'plan': credit_status['plan'],
                    'percentage': (new_remaining / credit_status['total']) * 100 if credit_status['total'] > 0 else 0
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to consume credits',
                    'plan': credit_status['plan']
                }
                
        except Exception as e:
            logger.error(f"Error consuming credits: {str(e)}")
            return {
                'success': False,
                'error': 'Credit system error',
                'plan': 'unknown'
            }

    def _get_credits_from_supabase(self, user_id: str) -> Dict[str, Any]:
        """Get user credits from Supabase"""
        try:
            from datetime import datetime, timedelta

            # Get today's usage
            today = datetime.now().date().isoformat()

            # Query today's credit usage
            usage_result = self.supabase.table('credit_usage').select('credits_consumed').eq('user_id', user_id).eq('date', today).execute()

            total_used_today = sum(record['credits_consumed'] for record in usage_result.data) if usage_result.data else 0

            # For now, assume free plan (50 daily credits)
            # TODO: Get actual plan from user subscription
            total_credits = 50
            remaining = max(0, total_credits - total_used_today)

            return {
                'plan': 'free',
                'type': 'daily',
                'remaining': remaining,
                'total': total_credits,
                'reset_date': (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
                'percentage': (remaining / total_credits) * 100 if total_credits > 0 else 0
            }

        except Exception as e:
            logger.error(f"❌ Error getting credits from Supabase: {str(e)}")
            # Return fallback
            return {
                'plan': 'free',
                'type': 'daily',
                'remaining': 50,
                'total': 50,
                'reset_date': None,
                'percentage': 100
            }
    
    def get_task_credit_cost(self, task_type: str) -> int:
        """Get credit cost for a specific task type"""
        return self.CREDIT_COSTS.get(task_type, 1)
    
    def get_credit_costs_display(self) -> Dict[str, Dict[str, int]]:
        """Get organized credit costs for display"""
        return {
            'Basic Tasks': {
                'Chat Message': self.CREDIT_COSTS['chat_message'],
                'Web Search': self.CREDIT_COSTS['simple_search'],
                'Text Generation': self.CREDIT_COSTS['text_generation']
            },
            'AI Agents': {
                'Code Wave (Simple)': self.CREDIT_COSTS['code_wave_simple'],
                'Code Wave (Advanced)': self.CREDIT_COSTS['code_wave_advanced'],
                'Agent Wave (Email)': self.CREDIT_COSTS['agent_wave_email'],
                'Agent Wave (SEO)': self.CREDIT_COSTS['agent_wave_seo'],
                'Research Lab': self.CREDIT_COSTS['research_basic']
            },
            'Prime Agent Tools': {
                'Job Search': self.CREDIT_COSTS['prime_agent_job_search'],
                'Travel Planning': self.CREDIT_COSTS['prime_agent_travel'],
                'Flight Search': self.CREDIT_COSTS['prime_agent_flight'],
                'Real Estate': self.CREDIT_COSTS['prime_agent_real_estate']
            },
            'Context 7 Tools (All 25 Tools)': {
                'Ride Booking': self.CREDIT_COSTS['context7_ride_booking'],
                'Flight Booking': self.CREDIT_COSTS['context7_flight_booking'],
                'Hotel Booking': self.CREDIT_COSTS['context7_hotel_booking'],
                'Job Search': self.CREDIT_COSTS['context7_job_search'],
                'Medical Appointment': self.CREDIT_COSTS['context7_medical_appointment'],
                'Government Services': self.CREDIT_COSTS['context7_government_services'],
                'Package Tracking': self.CREDIT_COSTS['context7_package_tracking'],
                'Financial Monitoring': self.CREDIT_COSTS['context7_financial_monitoring'],
                'Form Filling': self.CREDIT_COSTS['context7_form_filling'],
                'Business Plan': self.CREDIT_COSTS['context7_business_plan'],
                'Travel Planning': self.CREDIT_COSTS['context7_travel_planning'],
                'Pharmacy Search': self.CREDIT_COSTS['context7_pharmacy_search'],
                'Car Rental': self.CREDIT_COSTS['context7_car_rental'],
                'Fitness Services': self.CREDIT_COSTS['context7_fitness_services'],
                'Home Services': self.CREDIT_COSTS['context7_home_services'],
                'Legal Services': self.CREDIT_COSTS['context7_legal_services'],
                'Online Course Search': self.CREDIT_COSTS['context7_online_course_search'],
                'Banking Services': self.CREDIT_COSTS['context7_banking_services'],
                'Appliance Repair': self.CREDIT_COSTS['context7_appliance_repair'],
                'Gardening Services': self.CREDIT_COSTS['context7_gardening_services'],
                'Event Planning': self.CREDIT_COSTS['context7_event_planning'],
                'Auto Maintenance': self.CREDIT_COSTS['context7_auto_maintenance'],
                'Tech Support': self.CREDIT_COSTS['context7_tech_support'],
                'Cleaning Services': self.CREDIT_COSTS['context7_cleaning_services'],
                'Tutoring Services': self.CREDIT_COSTS['context7_tutoring_services']
            }
        }
    
    def reset_daily_credits(self, user_id: str) -> bool:
        """Reset daily credits for free plan users"""
        try:
            if not self.db:
                # Fallback mode - reset in-memory storage
                return self._reset_daily_credits_fallback(user_id)

            user_plan = self.db.get_user_subscription(user_id)
            plan_name = user_plan.get('plan_name', 'free') if user_plan else 'free'

            if plan_name == 'free':
                return self.db.reset_daily_credits(user_id)

            return True  # Non-free plans don't need daily reset

        except Exception as e:
            logger.error(f"Error resetting daily credits: {str(e)}")
            return False

    def _consume_credits_supabase(self, user_id: str, task_type: str, amount: int) -> bool:
        """Consume credits using Supabase"""
        try:
            from datetime import datetime

            # Log credit usage in Supabase
            usage_data = {
                'user_id': user_id,
                'task_type': task_type,
                'credits_consumed': amount,
                'timestamp': datetime.utcnow().isoformat(),
                'date': datetime.utcnow().date().isoformat()
            }

            # Insert usage record
            result = self.supabase.table('credit_usage').insert(usage_data).execute()

            if result.data:
                logger.info(f"✅ Consumed {amount} credits for {task_type} (user: {user_id}, Supabase)")
                return True
            else:
                logger.error(f"❌ Failed to log credit usage in Supabase")
                return False

        except Exception as e:
            logger.error(f"❌ Error consuming credits in Supabase: {str(e)}")
            return False

    def _consume_credits_fallback(self, user_id: str, amount: int, task_type: str) -> bool:
        """Fallback method to consume credits when database is unavailable"""
        try:
            # Initialize storage if needed
            if not hasattr(self, '_usage_storage'):
                self._usage_storage = {}

            today = datetime.now().date().isoformat()
            key = f"{user_id}_{today}"

            if key not in self._usage_storage:
                self._usage_storage[key] = 0

            self._usage_storage[key] += amount
            logger.info(f"Consumed {amount} credits for {task_type} (user: {user_id}, fallback mode)")
            return True

        except Exception as e:
            logger.error(f"Error in fallback credit consumption: {str(e)}")
            return False

    def _reset_daily_credits_fallback(self, user_id: str) -> bool:
        """Reset daily credits in fallback mode"""
        try:
            if not hasattr(self, '_usage_storage'):
                return True

            today = datetime.now().date().isoformat()
            key = f"{user_id}_{today}"

            if key in self._usage_storage:
                del self._usage_storage[key]

            logger.info(f"Reset daily credits for user {user_id} (fallback mode)")
            return True

        except Exception as e:
            logger.error(f"Error resetting daily credits (fallback): {str(e)}")
            return False

    def get_daily_usage_fallback(self, user_id: str) -> int:
        """Get daily usage from fallback storage"""
        try:
            if not hasattr(self, '_usage_storage'):
                return 0

            today = datetime.now().date().isoformat()
            key = f"{user_id}_{today}"
            return self._usage_storage.get(key, 0)

        except Exception as e:
            logger.error(f"Error getting fallback usage: {str(e)}")
            return 0

# Global instance
credit_service = CreditService()
