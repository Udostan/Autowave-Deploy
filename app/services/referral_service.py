"""
AutoWave Influencer Referral System
Comprehensive referral tracking with UTM parameters and custom codes
"""

import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logging.warning("Supabase not available. Referral features will be disabled.")

logger = logging.getLogger(__name__)

@dataclass
class ReferralData:
    """Data class for referral information"""
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None
    referral_code: Optional[str] = None
    influencer_id: Optional[str] = None
    discount_percentage: float = 0.0
    bonus_credits: int = 0
    created_at: Optional[datetime] = None

@dataclass
class InfluencerProfile:
    """Data class for influencer information"""
    id: str
    name: str
    email: str
    utm_source: str
    referral_code: str
    discount_percentage: float
    bonus_credits: int
    commission_rate: float
    is_active: bool
    total_referrals: int = 0
    total_revenue: float = 0.0
    created_at: Optional[datetime] = None

class ReferralService:
    """
    Comprehensive referral service for AutoWave influencer program.
    Supports UTM tracking, custom codes, and commission management.
    """
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.use_supabase = False
        
        if SUPABASE_AVAILABLE:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client for referral tracking."""
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            
            if supabase_url and supabase_key:
                self.client = create_client(supabase_url, supabase_key)
                self.use_supabase = True
                logger.info("✅ Referral service initialized with Supabase")
            else:
                logger.warning("Supabase credentials not found. Using fallback mode.")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
    
    def parse_utm_parameters(self, url: str) -> Dict[str, str]:
        """
        Parse UTM parameters from URL.
        
        Args:
            url: Full URL with potential UTM parameters
            
        Returns:
            Dictionary of UTM parameters
        """
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            utm_params = {}
            utm_keys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']
            
            for key in utm_keys:
                if key in query_params:
                    utm_params[key] = query_params[key][0]  # Get first value
            
            return utm_params
        except Exception as e:
            logger.error(f"Error parsing UTM parameters: {e}")
            return {}
    
    def get_influencer_by_utm_source(self, utm_source: str) -> Optional[InfluencerProfile]:
        """
        Get influencer profile by UTM source.
        
        Args:
            utm_source: UTM source parameter (e.g., 'MatthewBerman')
            
        Returns:
            InfluencerProfile if found, None otherwise
        """
        if not self.use_supabase:
            return self._get_fallback_influencer(utm_source)
        
        try:
            result = self.client.table('influencers').select('*').eq('utm_source', utm_source).eq('is_active', True).single().execute()
            
            if result.data:
                return InfluencerProfile(**result.data)
            
        except Exception as e:
            logger.error(f"Error fetching influencer by UTM source: {e}")
        
        return None
    
    def get_influencer_by_code(self, referral_code: str) -> Optional[InfluencerProfile]:
        """
        Get influencer profile by referral code.
        
        Args:
            referral_code: Custom referral code (e.g., 'MATTHEW20')
            
        Returns:
            InfluencerProfile if found, None otherwise
        """
        if not self.use_supabase:
            return self._get_fallback_influencer_by_code(referral_code)
        
        try:
            result = self.client.table('influencers').select('*').eq('referral_code', referral_code.upper()).eq('is_active', True).single().execute()
            
            if result.data:
                return InfluencerProfile(**result.data)
            
        except Exception as e:
            logger.error(f"Error fetching influencer by code: {e}")
        
        return None
    
    def process_referral(self, utm_params: Dict[str, str] = None, referral_code: str = None) -> ReferralData:
        """
        Process referral data from UTM parameters or referral code.
        
        Args:
            utm_params: Dictionary of UTM parameters
            referral_code: Custom referral code
            
        Returns:
            ReferralData object with discount and bonus information
        """
        referral_data = ReferralData(created_at=datetime.utcnow())
        
        # Process UTM parameters
        if utm_params:
            referral_data.utm_source = utm_params.get('utm_source')
            referral_data.utm_medium = utm_params.get('utm_medium')
            referral_data.utm_campaign = utm_params.get('utm_campaign')
            referral_data.utm_content = utm_params.get('utm_content')
            referral_data.utm_term = utm_params.get('utm_term')
            
            # Get influencer by UTM source
            if referral_data.utm_source:
                influencer = self.get_influencer_by_utm_source(referral_data.utm_source)
                if influencer:
                    referral_data.influencer_id = influencer.id
                    referral_data.discount_percentage = influencer.discount_percentage
                    referral_data.bonus_credits = influencer.bonus_credits
                    referral_data.referral_code = influencer.referral_code
        
        # Process referral code (takes precedence over UTM)
        if referral_code:
            influencer = self.get_influencer_by_code(referral_code)
            if influencer:
                referral_data.influencer_id = influencer.id
                referral_data.referral_code = referral_code.upper()
                referral_data.discount_percentage = influencer.discount_percentage
                referral_data.bonus_credits = influencer.bonus_credits
        
        return referral_data
    
    def track_referral_visit(self, referral_data: ReferralData, user_id: str = None, ip_address: str = None) -> bool:
        """
        Track a referral visit for analytics.
        
        Args:
            referral_data: ReferralData object
            user_id: User ID if available
            ip_address: Visitor IP address
            
        Returns:
            True if tracked successfully
        """
        if not self.use_supabase:
            return True  # Fallback mode
        
        try:
            visit_data = {
                'influencer_id': referral_data.influencer_id,
                'utm_source': referral_data.utm_source,
                'utm_medium': referral_data.utm_medium,
                'utm_campaign': referral_data.utm_campaign,
                'utm_content': referral_data.utm_content,
                'utm_term': referral_data.utm_term,
                'referral_code': referral_data.referral_code,
                'user_id': user_id,
                'ip_address': ip_address,
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.client.table('referral_visits').insert(visit_data).execute()
            return True
            
        except Exception as e:
            logger.error(f"Error tracking referral visit: {e}")
            return False
    
    def track_referral_conversion(self, referral_data: ReferralData, user_id: str, subscription_id: str, amount: float) -> bool:
        """
        Track a successful referral conversion (subscription purchase).
        
        Args:
            referral_data: ReferralData object
            user_id: User ID who made the purchase
            subscription_id: Subscription ID
            amount: Purchase amount
            
        Returns:
            True if tracked successfully
        """
        if not self.use_supabase:
            return True  # Fallback mode
        
        try:
            conversion_data = {
                'influencer_id': referral_data.influencer_id,
                'user_id': user_id,
                'subscription_id': subscription_id,
                'referral_code': referral_data.referral_code,
                'utm_source': referral_data.utm_source,
                'utm_medium': referral_data.utm_medium,
                'utm_campaign': referral_data.utm_campaign,
                'amount': amount,
                'discount_applied': referral_data.discount_percentage,
                'bonus_credits_given': referral_data.bonus_credits,
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.client.table('referral_conversions').insert(conversion_data).execute()
            
            # Update influencer stats
            if referral_data.influencer_id:
                self._update_influencer_stats(referral_data.influencer_id, amount)
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking referral conversion: {e}")
            return False
    
    def _update_influencer_stats(self, influencer_id: str, amount: float):
        """Update influencer statistics after a conversion."""
        try:
            # Get current stats
            result = self.client.table('influencers').select('total_referrals, total_revenue').eq('id', influencer_id).single().execute()
            
            if result.data:
                new_referrals = result.data.get('total_referrals', 0) + 1
                new_revenue = result.data.get('total_revenue', 0.0) + amount
                
                # Update stats
                self.client.table('influencers').update({
                    'total_referrals': new_referrals,
                    'total_revenue': new_revenue,
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('id', influencer_id).execute()
                
        except Exception as e:
            logger.error(f"Error updating influencer stats: {e}")
    
    def _get_fallback_influencer(self, utm_source: str) -> Optional[InfluencerProfile]:
        """Fallback influencer data when Supabase is not available."""
        # Generic partner data for testing
        fallback_influencers = {
            'TechPartnerA': InfluencerProfile(
                id='partner-001',
                name='Tech Partner A',
                email='partner-a@autowave.pro',
                utm_source='TechPartnerA',
                referral_code='TECH20',
                discount_percentage=20.0,
                bonus_credits=100,
                commission_rate=10.0,
                is_active=True
            ),
            'AIPartnerB': InfluencerProfile(
                id='partner-002',
                name='AI Partner B',
                email='partner-b@autowave.pro',
                utm_source='AIPartnerB',
                referral_code='AI15',
                discount_percentage=15.0,
                bonus_credits=50,
                commission_rate=8.0,
                is_active=True
            ),
            'PremiumPartnerC': InfluencerProfile(
                id='partner-003',
                name='Premium Partner C',
                email='partner-c@autowave.pro',
                utm_source='PremiumPartnerC',
                referral_code='PREMIUM30',
                discount_percentage=30.0,
                bonus_credits=150,
                commission_rate=12.0,
                is_active=True
            )
        }

        return fallback_influencers.get(utm_source)
    
    def _get_fallback_influencer_by_code(self, referral_code: str) -> Optional[InfluencerProfile]:
        """Fallback influencer data by code when Supabase is not available."""
        code_mapping = {
            'TECH20': 'TechPartnerA',
            'AI15': 'AIPartnerB',
            'PREMIUM30': 'PremiumPartnerC'
        }

        utm_source = code_mapping.get(referral_code.upper())
        if utm_source:
            return self._get_fallback_influencer(utm_source)

        return None
    
    def generate_referral_link(self, influencer_id: str, base_url: str = "https://autowave.pro") -> str:
        """
        Generate a referral link for an influencer.
        
        Args:
            influencer_id: Influencer ID
            base_url: Base URL for the platform
            
        Returns:
            Complete referral URL with UTM parameters
        """
        if not self.use_supabase:
            return f"{base_url}/?utm_source=TechPartnerA&utm_medium=Youtube&utm_campaign=partnership"
        
        try:
            result = self.client.table('influencers').select('*').eq('id', influencer_id).single().execute()
            
            if result.data:
                influencer = InfluencerProfile(**result.data)
                return f"{base_url}/?utm_source={influencer.utm_source}&utm_medium=Youtube&utm_campaign=influence&utm_content={influencer.referral_code}"
            
        except Exception as e:
            logger.error(f"Error generating referral link: {e}")
        
        return f"{base_url}/?utm_source=Unknown&utm_medium=Direct&utm_campaign=referral"
    
    def get_influencer_dashboard_data(self, influencer_id: str) -> Dict[str, Any]:
        """
        Get dashboard data for an influencer.
        
        Args:
            influencer_id: Influencer ID
            
        Returns:
            Dictionary with dashboard metrics
        """
        if not self.use_supabase:
            return {
                'total_visits': 0,
                'total_conversions': 0,
                'total_revenue': 0.0,
                'conversion_rate': 0.0,
                'commission_earned': 0.0
            }
        
        try:
            # Get visit count
            visits_result = self.client.table('referral_visits').select('id').eq('influencer_id', influencer_id).execute()
            total_visits = len(visits_result.data) if visits_result.data else 0
            
            # Get conversion data
            conversions_result = self.client.table('referral_conversions').select('amount').eq('influencer_id', influencer_id).execute()
            total_conversions = len(conversions_result.data) if conversions_result.data else 0
            total_revenue = sum(item['amount'] for item in conversions_result.data) if conversions_result.data else 0.0
            
            # Get influencer commission rate
            influencer_result = self.client.table('influencers').select('commission_rate').eq('id', influencer_id).single().execute()
            commission_rate = influencer_result.data.get('commission_rate', 0.0) if influencer_result.data else 0.0
            
            conversion_rate = (total_conversions / total_visits * 100) if total_visits > 0 else 0.0
            commission_earned = total_revenue * (commission_rate / 100)
            
            return {
                'total_visits': total_visits,
                'total_conversions': total_conversions,
                'total_revenue': total_revenue,
                'conversion_rate': round(conversion_rate, 2),
                'commission_earned': round(commission_earned, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting influencer dashboard data: {e}")
            return {
                'total_visits': 0,
                'total_conversions': 0,
                'total_revenue': 0.0,
                'conversion_rate': 0.0,
                'commission_earned': 0.0
            }
