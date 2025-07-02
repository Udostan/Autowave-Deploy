"""
AutoWave Coupon Service
Handles coupon code validation, discount application, and promotional campaigns
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class CouponType(Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    FREE_CREDITS = "free_credits"
    FREE_TRIAL = "free_trial"

class CouponStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    USED = "used"
    DISABLED = "disabled"

@dataclass
class Coupon:
    code: str
    type: CouponType
    value: float  # Percentage (0-100) or fixed amount in USD
    description: str
    max_uses: int
    current_uses: int
    valid_from: datetime
    valid_until: datetime
    status: CouponStatus
    applicable_plans: List[str]  # ['free', 'plus', 'pro'] or ['all']
    minimum_amount: float  # Minimum order amount to apply coupon
    created_by: str
    created_at: datetime
    metadata: Dict[str, Any]

class CouponService:
    """Service for managing coupon codes and discounts"""
    
    def __init__(self):
        # In-memory storage for demo (replace with database in production)
        self.coupons = self._initialize_default_coupons()
        self.usage_history = []
        
    def _initialize_default_coupons(self) -> Dict[str, Coupon]:
        """Initialize default promotional coupons"""
        now = datetime.now()
        
        return {
            # Influencer/Affiliate Coupons (20-30% discount)
            "AUTOWAVE20": Coupon(
                code="AUTOWAVE20",
                type=CouponType.PERCENTAGE,
                value=20.0,
                description="20% off for new users - Influencer promotion",
                max_uses=1000,
                current_uses=0,
                valid_from=now,
                valid_until=now + timedelta(days=90),
                status=CouponStatus.ACTIVE,
                applicable_plans=["plus", "pro"],
                minimum_amount=10.0,
                created_by="admin",
                created_at=now,
                metadata={"campaign": "influencer_promo", "tier": "standard"}
            ),
            
            "CREATOR30": Coupon(
                code="CREATOR30",
                type=CouponType.PERCENTAGE,
                value=30.0,
                description="30% off for content creators - Premium promotion",
                max_uses=500,
                current_uses=0,
                valid_from=now,
                valid_until=now + timedelta(days=60),
                status=CouponStatus.ACTIVE,
                applicable_plans=["pro"],
                minimum_amount=50.0,
                created_by="admin",
                created_at=now,
                metadata={"campaign": "creator_program", "tier": "premium"}
            ),
            
            # Launch/Event Coupons (15-25% discount)
            "LAUNCH25": Coupon(
                code="LAUNCH25",
                type=CouponType.PERCENTAGE,
                value=25.0,
                description="25% off - Product launch celebration",
                max_uses=2000,
                current_uses=0,
                valid_from=now,
                valid_until=now + timedelta(days=30),
                status=CouponStatus.ACTIVE,
                applicable_plans=["plus", "pro"],
                minimum_amount=0.0,
                created_by="admin",
                created_at=now,
                metadata={"campaign": "product_launch", "tier": "event"}
            ),
            
            # First-time User Coupons (10-15% discount)
            "WELCOME15": Coupon(
                code="WELCOME15",
                type=CouponType.PERCENTAGE,
                value=15.0,
                description="15% off for first-time subscribers",
                max_uses=5000,
                current_uses=0,
                valid_from=now,
                valid_until=now + timedelta(days=365),
                status=CouponStatus.ACTIVE,
                applicable_plans=["plus", "pro"],
                minimum_amount=0.0,
                created_by="admin",
                created_at=now,
                metadata={"campaign": "welcome_offer", "tier": "standard"}
            ),
            
            # Credit Bonus Coupons
            "BONUS1000": Coupon(
                code="BONUS1000",
                type=CouponType.FREE_CREDITS,
                value=1000.0,
                description="1000 free credits bonus",
                max_uses=1000,
                current_uses=0,
                valid_from=now,
                valid_until=now + timedelta(days=180),
                status=CouponStatus.ACTIVE,
                applicable_plans=["plus", "pro"],
                minimum_amount=0.0,
                created_by="admin",
                created_at=now,
                metadata={"campaign": "credit_bonus", "tier": "standard"}
            ),
            
            # Fixed Amount Coupons
            "SAVE10": Coupon(
                code="SAVE10",
                type=CouponType.FIXED_AMOUNT,
                value=10.0,
                description="$10 off your subscription",
                max_uses=500,
                current_uses=0,
                valid_from=now,
                valid_until=now + timedelta(days=120),
                status=CouponStatus.ACTIVE,
                applicable_plans=["plus", "pro"],
                minimum_amount=25.0,
                created_by="admin",
                created_at=now,
                metadata={"campaign": "fixed_discount", "tier": "standard"}
            )
        }
    
    def validate_coupon(self, code: str, plan_name: str, amount: float, user_id: str = None) -> Dict[str, Any]:
        """Validate a coupon code and return discount information"""
        try:
            code = code.upper().strip()
            
            if code not in self.coupons:
                return {
                    'valid': False,
                    'error': 'Invalid coupon code',
                    'discount_amount': 0,
                    'final_amount': amount
                }
            
            coupon = self.coupons[code]
            
            # Check if coupon is active
            if coupon.status != CouponStatus.ACTIVE:
                return {
                    'valid': False,
                    'error': 'Coupon is no longer active',
                    'discount_amount': 0,
                    'final_amount': amount
                }
            
            # Check validity dates
            now = datetime.now()
            if now < coupon.valid_from or now > coupon.valid_until:
                return {
                    'valid': False,
                    'error': 'Coupon has expired',
                    'discount_amount': 0,
                    'final_amount': amount
                }
            
            # Check usage limits
            if coupon.current_uses >= coupon.max_uses:
                return {
                    'valid': False,
                    'error': 'Coupon usage limit reached',
                    'discount_amount': 0,
                    'final_amount': amount
                }
            
            # Check applicable plans
            if 'all' not in coupon.applicable_plans and plan_name not in coupon.applicable_plans:
                return {
                    'valid': False,
                    'error': f'Coupon not applicable to {plan_name} plan',
                    'discount_amount': 0,
                    'final_amount': amount
                }
            
            # Check minimum amount
            if amount < coupon.minimum_amount:
                return {
                    'valid': False,
                    'error': f'Minimum order amount is ${coupon.minimum_amount:.2f}',
                    'discount_amount': 0,
                    'final_amount': amount
                }
            
            # Calculate discount
            discount_amount = self._calculate_discount(coupon, amount)
            final_amount = max(0, amount - discount_amount)
            
            return {
                'valid': True,
                'coupon': {
                    'code': coupon.code,
                    'type': coupon.type.value,
                    'value': coupon.value,
                    'description': coupon.description
                },
                'discount_amount': discount_amount,
                'final_amount': final_amount,
                'savings_percentage': (discount_amount / amount * 100) if amount > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error validating coupon {code}: {str(e)}")
            return {
                'valid': False,
                'error': 'Failed to validate coupon',
                'discount_amount': 0,
                'final_amount': amount
            }
    
    def _calculate_discount(self, coupon: Coupon, amount: float) -> float:
        """Calculate discount amount based on coupon type"""
        if coupon.type == CouponType.PERCENTAGE:
            return amount * (coupon.value / 100)
        elif coupon.type == CouponType.FIXED_AMOUNT:
            return min(coupon.value, amount)  # Don't exceed the order amount
        elif coupon.type == CouponType.FREE_CREDITS:
            # For credit coupons, return 0 discount on price but handle credits separately
            return 0
        else:
            return 0
    
    def apply_coupon(self, code: str, plan_name: str, amount: float, user_id: str) -> Dict[str, Any]:
        """Apply a coupon and record usage"""
        try:
            validation = self.validate_coupon(code, plan_name, amount, user_id)
            
            if not validation['valid']:
                return validation
            
            code = code.upper().strip()
            coupon = self.coupons[code]
            
            # Record usage
            usage_record = {
                'coupon_code': code,
                'user_id': user_id,
                'plan_name': plan_name,
                'original_amount': amount,
                'discount_amount': validation['discount_amount'],
                'final_amount': validation['final_amount'],
                'used_at': datetime.now(),
                'metadata': coupon.metadata
            }
            
            self.usage_history.append(usage_record)
            
            # Increment usage count
            coupon.current_uses += 1
            
            # Handle special coupon types
            if coupon.type == CouponType.FREE_CREDITS:
                validation['bonus_credits'] = int(coupon.value)
            
            validation['applied'] = True
            logger.info(f"Applied coupon {code} for user {user_id}: ${validation['discount_amount']:.2f} discount")
            
            return validation
            
        except Exception as e:
            logger.error(f"Error applying coupon {code}: {str(e)}")
            return {
                'valid': False,
                'applied': False,
                'error': 'Failed to apply coupon',
                'discount_amount': 0,
                'final_amount': amount
            }

# Global coupon service instance
coupon_service = CouponService()
