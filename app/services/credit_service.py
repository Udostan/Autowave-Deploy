"""
Credit Management Service for AutoWave
Handles credit consumption, tracking, and limits based on competitor analysis
"""

import os
import logging
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
# from .database_service import DatabaseService  # Not available, using fallback mode

# Try to import tiktoken for token counting, fallback to simple estimation
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

logger = logging.getLogger(__name__)

class CreditService:
    """Service for managing user credits and consumption tracking"""
    
    # Credit costs based on Genspark analysis (200 credits/day = ~6-7 credits per search)
    CREDIT_COSTS = {
        # Basic AI Tasks (Genspark-style: 1-2 credits per basic task)
        'chat_message': 1,
        'simple_search': 1,
        'text_generation': 1,
        'basic_query': 1,

        # AutoWave Chat (Genspark-style: 1-3 credits per chat)
        'autowave_chat_basic': 1,
        'autowave_chat_advanced': 3,

        # Code Wave (Website Creation) - High value tasks
        'code_wave_simple': 50,       # Reduced from 200 to 50
        'code_wave_advanced': 80,     # Reduced from 360 to 80
        'code_wave_complex': 150,     # Reduced from 900 to 150

        # Agent Wave (Document Processing) - Genspark-style
        'agent_wave_email': 3,
        'agent_wave_seo': 5,
        'agent_wave_learning': 8,
        'agent_wave_document': 4,

        # Prime Agent Tools - Genspark-style pricing (2-8 credits per task)
        'prime_agent_basic': 2,
        'prime_agent_complex': 6,
        'prime_agent_visual_browser': 8,
        'prime_agent_multi_tool': 10,  # Multi-tool orchestration costs more
        'prime_agent_job_search': 3,
        'prime_agent_travel': 4,
        'prime_agent_real_estate': 3,
        'prime_agent_weather': 1,
        'prime_agent_news': 2,
        'prime_agent_flight': 5,
        'prime_agent_hotel': 4,

        # Research Lab - Genspark-style pricing (3-12 credits per research)
        'research_basic': 3,
        'research_advanced': 8,
        'research_deep_analysis': 12,
        
        # File Processing
        'file_upload_small': 5,
        'file_upload_medium': 10,
        'file_upload_large': 20,
        
        # Web Browsing
        'web_browse_page': 8,
        'web_browse_multiple': 15,
        'web_scraping': 12,

        # Context 7 Tools (Prime Agent Tools) - All 25 Tools (Genspark-style: 2-8 credits)
        'context7_ride_booking': 3,
        'context7_flight_booking': 5,
        'context7_hotel_booking': 4,
        'context7_job_search': 6,
        'context7_medical_appointment': 5,
        'context7_government_services': 4,
        'context7_package_tracking': 3,
        'context7_financial_monitoring': 5,
        'context7_form_filling': 4,
        'context7_business_plan': 8,
        'context7_travel_planning': 6,
        'context7_pharmacy_search': 4,
        'context7_car_rental': 5,
        'context7_fitness_services': 4,
        'context7_home_services': 5,
        'context7_legal_services': 6,

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

    def count_tokens(self, text: str, model: str = "gpt-3.5-turbo") -> int:
        """Count tokens in text using tiktoken or fallback estimation"""
        if not text:
            return 0

        if TIKTOKEN_AVAILABLE:
            try:
                encoding = tiktoken.encoding_for_model(model)
                return len(encoding.encode(text))
            except Exception as e:
                logger.warning(f"Tiktoken error: {e}, using fallback estimation")

        # Fallback: rough estimation (1 token ≈ 4 characters for English)
        return max(1, len(text) // 4)

    def calculate_token_based_credits(self,
                                    input_text: str = "",
                                    output_text: str = "",
                                    task_type: str = "autowave_chat",
                                    execution_time_minutes: float = 0,
                                    tool_calls: int = 0,
                                    image_count: int = 0) -> Dict[str, Any]:
        """
        Calculate credits based on actual token usage (Genspark/Manus style)

        Args:
            input_text: User input text
            output_text: AI response text
            task_type: Type of task for minimum charge
            execution_time_minutes: Time spent on task execution
            tool_calls: Number of tool/API calls made
            image_count: Number of images processed

        Returns:
            Dict with credit breakdown and total
        """

        # Count tokens
        input_tokens = self.count_tokens(input_text)
        output_tokens = self.count_tokens(output_text)

        # Calculate credit components (matching Manus/Genspark rates)
        input_credits = input_tokens * 0.001      # 1 credit per 1000 input tokens
        output_credits = output_tokens * 0.002    # 1 credit per 500 output tokens
        tool_credits = tool_calls * 0.5           # 0.5 credits per tool call
        time_credits = execution_time_minutes * 0.1  # 0.1 credits per minute
        image_credits = image_count * 0.01        # 0.01 credits per image

        # Calculate total
        calculated_credits = input_credits + output_credits + tool_credits + time_credits + image_credits

        # Apply minimum charge based on task type
        base_minimums = {
            'autowave_chat': 0.5,
            'prime_agent': 1.0,
            'research_lab': 2.0,
            'agent_wave': 1.0,
            'design': 0.5,
            'context7_tools': 2.0,
        }

        # Extract base task type
        base_task = task_type.split('_')[0] + '_' + task_type.split('_')[1] if '_' in task_type else task_type
        minimum_charge = base_minimums.get(base_task, 1.0)

        # Use the higher of calculated credits or minimum charge
        final_credits = max(calculated_credits, minimum_charge)

        return {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'input_credits': round(input_credits, 3),
            'output_credits': round(output_credits, 3),
            'tool_credits': round(tool_credits, 3),
            'time_credits': round(time_credits, 3),
            'image_credits': round(image_credits, 3),
            'calculated_credits': round(calculated_credits, 3),
            'minimum_charge': minimum_charge,
            'final_credits': round(final_credits, 3),
            'billing_method': 'token_based'
        }

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
    
    def consume_credits(self, user_id: str, task_type: str, amount: Optional[float] = None,
                       input_text: str = "", output_text: str = "",
                       execution_time_minutes: float = 0, tool_calls: int = 0,
                       image_count: int = 0, use_token_based: bool = True) -> Dict[str, Any]:
        """
        Consume credits for a specific task with token-based calculation

        Args:
            user_id: User identifier
            task_type: Type of task being performed
            amount: Fixed amount to charge (overrides token calculation)
            input_text: User input text for token counting
            output_text: AI response text for token counting
            execution_time_minutes: Time spent on task execution
            tool_calls: Number of tool/API calls made
            image_count: Number of images processed
            use_token_based: Whether to use token-based calculation (default: True)
        """
        try:
            # Calculate credits based on method
            if amount is not None:
                # Fixed amount specified
                credit_cost = amount
                credit_breakdown = {
                    'final_credits': amount,
                    'billing_method': 'fixed_amount'
                }
            elif use_token_based and (input_text or output_text or tool_calls > 0 or execution_time_minutes > 0):
                # Use token-based calculation (Genspark/Manus style)
                credit_breakdown = self.calculate_token_based_credits(
                    input_text=input_text,
                    output_text=output_text,
                    task_type=task_type,
                    execution_time_minutes=execution_time_minutes,
                    tool_calls=tool_calls,
                    image_count=image_count
                )
                credit_cost = credit_breakdown['final_credits']
            else:
                # Fallback to fixed cost
                credit_cost = self.CREDIT_COSTS.get(task_type, 1)
                credit_breakdown = {
                    'final_credits': credit_cost,
                    'billing_method': 'fixed_fallback'
                }

            # Get user's current credits
            credit_status = self.get_user_credits(user_id)

            # Debug logging
            logger.info(f"💳 Credit consumption attempt - User: {user_id}, Task: {task_type}, Cost: {credit_cost}, Status: {credit_status}")

            # Check if user has unlimited credits (skip for testing if CREDIT_DEBUG_MODE is set)
            import os
            debug_mode = os.getenv('CREDIT_DEBUG_MODE', 'false').lower() == 'true'

            if credit_status['type'] == 'unlimited' and not debug_mode:
                # Log usage but don't deduct
                if self.db:
                    self.db.log_credit_usage(user_id, task_type, credit_cost, 'unlimited')
                logger.info(f"💳 Admin unlimited credits - logged usage only")
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
                if not success:
                    # Fallback to in-memory tracking if Supabase fails (e.g., RLS policy issues)
                    logger.warning(f"💳 Supabase failed, using fallback tracking for user {user_id}")
                    success = self._consume_credits_fallback(user_id, credit_cost, task_type)
            else:
                # Fallback mode - use in-memory storage
                success = self._consume_credits_fallback(user_id, credit_cost, task_type)

            if success:
                new_remaining = credit_status['remaining'] - credit_cost
                result = {
                    'success': True,
                    'credits_consumed': credit_cost,
                    'remaining_credits': new_remaining,
                    'plan': credit_status['plan'],
                    'percentage': (new_remaining / credit_status['total']) * 100 if credit_status['total'] > 0 else 0
                }
                # Add credit breakdown if available
                if 'credit_breakdown' in locals():
                    result['credit_breakdown'] = credit_breakdown
                return result
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

            # Check if user_id is a valid UUID format (for real users)
            import re
            uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
            if not re.match(uuid_pattern, user_id, re.IGNORECASE):
                # Not a valid UUID, use fallback system
                logger.info(f"💳 User ID {user_id} is not a valid UUID, using fallback system")
                fallback_usage = self._get_fallback_usage(user_id)
                total_credits = 50
                remaining = max(0, total_credits - fallback_usage)

                return {
                    'plan': 'free',
                    'type': 'daily',
                    'remaining': remaining,
                    'total': total_credits,
                    'reset_date': (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
                    'percentage': (remaining / total_credits) * 100 if total_credits > 0 else 0
                }

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
            # Return fallback with actual usage tracking
            from datetime import datetime, timedelta
            fallback_usage = self._get_fallback_usage(user_id)
            total_credits = 50
            remaining = max(0, total_credits - fallback_usage)

            return {
                'plan': 'free',
                'type': 'daily',
                'remaining': remaining,
                'total': total_credits,
                'reset_date': (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
                'percentage': (remaining / total_credits) * 100 if total_credits > 0 else 0
            }

    def _consume_credits_supabase(self, user_id: str, task_type: str, credit_cost: int) -> bool:
        """Consume credits using Supabase"""
        try:
            from datetime import datetime

            # Log the credit usage
            usage_data = {
                'user_id': user_id,
                'task_type': task_type,
                'credits_consumed': credit_cost,
                'date': datetime.now().date().isoformat(),
                'timestamp': datetime.now().isoformat()
            }

            result = self.supabase.table('credit_usage').insert(usage_data).execute()

            if result.data:
                logger.info(f"💳 Supabase credit consumption logged: {credit_cost} credits for {task_type}")
                return True
            else:
                logger.error(f"💳 Failed to log credit consumption in Supabase")
                return False

        except Exception as e:
            logger.error(f"💳 Error consuming credits in Supabase: {str(e)}")
            return False

    def _consume_credits_fallback(self, user_id: str, credit_cost: int, task_type: str) -> bool:
        """Fallback credit consumption using file-based storage"""
        try:
            import os
            import json
            from datetime import datetime

            # Create fallback storage directory
            fallback_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'fallback_storage')
            os.makedirs(fallback_dir, exist_ok=True)

            fallback_file = os.path.join(fallback_dir, 'credit_usage.json')

            # Load existing usage data
            usage_data = {}
            if os.path.exists(fallback_file):
                try:
                    with open(fallback_file, 'r') as f:
                        usage_data = json.load(f)
                except:
                    usage_data = {}

            today = datetime.now().date().isoformat()
            key = f"{user_id}_{today}"

            current_usage = usage_data.get(key, 0)
            usage_data[key] = current_usage + credit_cost

            # Save updated usage data
            with open(fallback_file, 'w') as f:
                json.dump(usage_data, f)

            logger.info(f"💳 Fallback credit consumption: {credit_cost} credits for {task_type} (Total: {usage_data[key]})")
            return True

        except Exception as e:
            logger.error(f"💳 Error in fallback credit consumption: {str(e)}")
            return False

    def _get_fallback_usage(self, user_id: str) -> int:
        """Get current fallback usage for a user"""
        try:
            import os
            import json
            from datetime import datetime

            fallback_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'fallback_storage')
            fallback_file = os.path.join(fallback_dir, 'credit_usage.json')

            if not os.path.exists(fallback_file):
                return 0

            with open(fallback_file, 'r') as f:
                usage_data = json.load(f)

            today = datetime.now().date().isoformat()
            key = f"{user_id}_{today}"

            return usage_data.get(key, 0)

        except Exception as e:
            logger.error(f"💳 Error getting fallback usage: {str(e)}")
            return 0

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



# Global instance
credit_service = CreditService()
