"""
AutoWave Payment Gateway Service
Supports both Paystack and Stripe with unified interface
"""

import os
import logging
import requests
import stripe
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import json
from .currency_service import currency_service

logger = logging.getLogger(__name__)

class PaymentGateway(ABC):
    """Abstract payment gateway interface"""
    
    @abstractmethod
    def create_customer(self, email: str, name: str) -> Dict[str, Any]:
        """Create a customer in the payment gateway"""
        pass
    
    @abstractmethod
    def create_subscription(self, customer_id: str, plan_id: str, billing_cycle: str) -> Dict[str, Any]:
        """Create a subscription"""
        pass
    
    @abstractmethod
    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel a subscription"""
        pass
    
    @abstractmethod
    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription details"""
        pass
    
    @abstractmethod
    def verify_webhook(self, payload: str, signature: str) -> bool:
        """Verify webhook signature"""
        pass
    
    @abstractmethod
    def handle_webhook(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle webhook events"""
        pass

class PaystackGateway(PaymentGateway):
    """Paystack payment gateway implementation"""
    
    def __init__(self):
        self.secret_key = os.getenv('PAYSTACK_SECRET_KEY')
        self.public_key = os.getenv('PAYSTACK_PUBLIC_KEY')

        # Check if we're in test mode (placeholder keys or test keys)
        self.test_mode = (not self.secret_key or
                         self.secret_key.startswith('your_') or
                         self.secret_key.startswith('sk_test_your_') or
                         self.secret_key.startswith('sk_test_'))

        # Check if we're using live keys
        self.live_mode = self.secret_key.startswith('sk_live_')

        if self.test_mode:
            logger.info("Paystack running in test mode (placeholder keys)")
        elif self.live_mode:
            logger.info("Paystack running in LIVE mode - real payments will be processed")
        else:
            logger.warning("Paystack key format not recognized")

        self.base_url = 'https://api.paystack.co'
        self.headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }
    
    def create_customer(self, email: str, name: str) -> Dict[str, Any]:
        """Create a Paystack customer"""
        try:
            # In test mode, return mock customer
            if self.test_mode:
                mock_customer_id = f"CUS_test_{email.replace('@', '_').replace('.', '_')}"
                logger.info(f"Created mock Paystack customer: {mock_customer_id}")
                return {
                    'success': True,
                    'customer_id': mock_customer_id,
                    'data': {
                        'customer_code': mock_customer_id,
                        'email': email,
                        'first_name': name.split(' ')[0] if name else '',
                        'last_name': ' '.join(name.split(' ')[1:]) if len(name.split(' ')) > 1 else ''
                    }
                }

            data = {
                'email': email,
                'first_name': name.split(' ')[0] if name else '',
                'last_name': ' '.join(name.split(' ')[1:]) if len(name.split(' ')) > 1 else ''
            }

            response = requests.post(
                f'{self.base_url}/customer',
                headers=self.headers,
                json=data
            )

            result = response.json()

            if result.get('status'):
                return {
                    'success': True,
                    'customer_id': result['data']['customer_code'],
                    'data': result['data']
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', 'Failed to create customer')
                }

        except Exception as e:
            logger.error(f"Paystack create customer error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_subscription(self, customer_id: str, plan_id: str, billing_cycle: str) -> Dict[str, Any]:
        """Create a Paystack subscription with currency conversion"""
        try:
            # In test mode, return mock subscription with payment URL
            if self.test_mode:
                mock_subscription_id = f"SUB_test_{customer_id}_{plan_id}_{billing_cycle}"
                mock_authorization_url = f"https://checkout.paystack.com/test_{mock_subscription_id}"
                logger.info(f"Created mock Paystack subscription: {mock_subscription_id}")
                return {
                    'success': True,
                    'subscription_id': mock_subscription_id,
                    'authorization_url': mock_authorization_url,
                    'paystack_plan_code': f"autowave_{plan_id}_{billing_cycle}",
                    'data': {
                        'subscription_code': mock_subscription_id,
                        'status': 'active',
                        'customer': customer_id,
                        'plan': f"autowave_{plan_id}_{billing_cycle}",
                        'authorization_url': mock_authorization_url
                    }
                }

            # First, create or get the plan in NGN
            paystack_plan_result = self.create_or_get_plan(plan_id, billing_cycle)

            if not paystack_plan_result['success']:
                return paystack_plan_result

            paystack_plan_code = paystack_plan_result['plan_code']

            data = {
                'customer': customer_id,
                'plan': paystack_plan_code,
                'authorization': customer_id  # Will need authorization code from frontend
            }

            response = requests.post(
                f'{self.base_url}/subscription',
                headers=self.headers,
                json=data
            )

            result = response.json()

            if result.get('status'):
                return {
                    'success': True,
                    'subscription_id': result['data']['subscription_code'],
                    'authorization_url': result['data'].get('authorization_url'),
                    'paystack_plan_code': paystack_plan_code,
                    'data': result['data']
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', 'Failed to create subscription')
                }

        except Exception as e:
            logger.error(f"Paystack create subscription error: {str(e)}")
            return {'success': False, 'error': str(e)}

    def initialize_payment(self, customer_email: str, amount: int, plan_name: str, billing_cycle: str) -> Dict[str, Any]:
        """Initialize a Paystack payment for subscription"""
        try:
            # In test mode, return mock payment initialization
            if self.test_mode and not self.live_mode:
                mock_reference = f"autowave_test_{plan_name}_{billing_cycle}_{int(time.time())}"
                mock_authorization_url = f"https://checkout.paystack.com/test_{mock_reference}"
                logger.info(f"Created mock Paystack payment: {mock_reference}")
                return {
                    'success': True,
                    'authorization_url': mock_authorization_url,
                    'access_code': f"test_access_{mock_reference}",
                    'reference': mock_reference
                }

            # Convert amount to kobo (Paystack uses kobo)
            amount_kobo = amount * 100

            data = {
                'email': customer_email,
                'amount': amount_kobo,
                'currency': 'NGN',
                'reference': f"autowave_{plan_name}_{billing_cycle}_{int(time.time())}",
                'callback_url': f"{os.getenv('APP_URL', 'http://localhost:5001')}/payment/callback",
                'metadata': {
                    'plan_name': plan_name,
                    'billing_cycle': billing_cycle,
                    'platform': 'autowave'
                },
                'logo': os.getenv('PAYSTACK_LOGO_URL', f"{os.getenv('APP_URL', 'http://localhost:5001')}/static/images/autowave-logo.png"),
                'split_code': None,
                'subaccount': None,
                'transaction_charge': None,
                'bearer': 'account',
                'channels': ['card', 'bank', 'ussd', 'qr', 'mobile_money', 'bank_transfer', 'apple_pay'],
                'label': f"AutoWave {plan_name.title()} Plan - {billing_cycle.title()}",
                'custom_fields': [
                    {
                        'display_name': 'Plan Type',
                        'variable_name': 'plan_type',
                        'value': f"{plan_name.title()} Plan"
                    },
                    {
                        'display_name': 'Billing Cycle',
                        'variable_name': 'billing_cycle',
                        'value': billing_cycle.title()
                    }
                ]
            }

            response = requests.post(
                f'{self.base_url}/transaction/initialize',
                headers=self.headers,
                json=data
            )

            result = response.json()

            if result.get('status'):
                return {
                    'success': True,
                    'authorization_url': result['data']['authorization_url'],
                    'access_code': result['data']['access_code'],
                    'reference': result['data']['reference']
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', 'Failed to initialize payment')
                }

        except Exception as e:
            logger.error(f"Paystack initialize payment error: {str(e)}")
            return {'success': False, 'error': str(e)}

    def create_or_get_plan(self, plan_id: str, billing_cycle: str) -> Dict[str, Any]:
        """Create or get a Paystack plan with NGN pricing"""
        try:
            # Generate Paystack plan code
            paystack_plan_code = f"autowave_{plan_id}_{billing_cycle}"

            # Check if plan already exists
            existing_plan = self.get_plan(paystack_plan_code)
            if existing_plan['success']:
                return {
                    'success': True,
                    'plan_code': paystack_plan_code,
                    'data': existing_plan['data']
                }

            # Get plan details from our database (optimized pricing)
            # Updated pricing for better profit margins and competitiveness
            plan_prices = {
                'plus-plan-id': {'monthly': 15, 'annual': 171},
                'pro-plan-id': {'monthly': 99, 'annual': 1188},
                'enterprise-plan-id': {'monthly': 299, 'annual': 3588}
            }

            if plan_id not in plan_prices:
                return {'success': False, 'error': f'Unknown plan: {plan_id}'}

            usd_price = plan_prices[plan_id][billing_cycle.replace('ly', '')]

            # Convert USD to NGN
            conversion = currency_service.convert_plan_price(usd_price, 'paystack', billing_cycle)
            ngn_price = conversion['converted_amount']

            # Create plan in Paystack
            plan_data = {
                'name': f"AutoWave {plan_id.replace('-plan-id', '').title()} Plan ({billing_cycle.title()})",
                'amount': int(ngn_price * 100),  # Convert to kobo
                'interval': 'monthly' if billing_cycle == 'monthly' else 'annually',
                'currency': 'NGN',
                'plan_code': paystack_plan_code,
                'description': f"AutoWave subscription plan - {conversion['display_price']} per {billing_cycle.replace('ly', '')}"
            }

            response = requests.post(
                f'{self.base_url}/plan',
                headers=self.headers,
                json=plan_data
            )

            result = response.json()

            if result.get('status'):
                logger.info(f"Created Paystack plan: {paystack_plan_code} for ₦{ngn_price:,.2f}")
                return {
                    'success': True,
                    'plan_code': paystack_plan_code,
                    'ngn_price': ngn_price,
                    'usd_price': usd_price,
                    'data': result['data']
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', 'Failed to create plan')
                }

        except Exception as e:
            logger.error(f"Error creating Paystack plan: {str(e)}")
            return {'success': False, 'error': str(e)}

    def get_plan(self, plan_code: str) -> Dict[str, Any]:
        """Get a Paystack plan by code"""
        try:
            response = requests.get(
                f'{self.base_url}/plan/{plan_code}',
                headers=self.headers
            )

            result = response.json()

            return {
                'success': result.get('status', False),
                'data': result.get('data', {}),
                'message': result.get('message', '')
            }

        except Exception as e:
            logger.error(f"Error getting Paystack plan: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel a Paystack subscription"""
        try:
            data = {'code': subscription_id, 'token': subscription_id}
            
            response = requests.post(
                f'{self.base_url}/subscription/disable',
                headers=self.headers,
                json=data
            )
            
            result = response.json()
            
            return {
                'success': result.get('status', False),
                'data': result.get('data', {}),
                'message': result.get('message', '')
            }
            
        except Exception as e:
            logger.error(f"Paystack cancel subscription error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get Paystack subscription details"""
        try:
            response = requests.get(
                f'{self.base_url}/subscription/{subscription_id}',
                headers=self.headers
            )
            
            result = response.json()
            
            return {
                'success': result.get('status', False),
                'data': result.get('data', {}),
                'message': result.get('message', '')
            }
            
        except Exception as e:
            logger.error(f"Paystack get subscription error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def verify_webhook(self, payload: str, signature: str) -> bool:
        """Verify Paystack webhook signature"""
        try:
            import hmac
            import hashlib
            
            webhook_secret = os.getenv('PAYSTACK_WEBHOOK_SECRET')
            computed_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()
            
            return hmac.compare_digest(computed_signature, signature)
            
        except Exception as e:
            logger.error(f"Paystack webhook verification error: {str(e)}")
            return False
    
    def handle_webhook(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Paystack webhook events"""
        try:
            event_type = event_data.get('event')
            data = event_data.get('data', {})
            
            if event_type == 'subscription.create':
                return self._handle_subscription_created(data)
            elif event_type == 'subscription.disable':
                return self._handle_subscription_cancelled(data)
            elif event_type == 'invoice.payment_failed':
                return self._handle_payment_failed(data)
            elif event_type == 'invoice.update':
                return self._handle_invoice_updated(data)
            
            return {'success': True, 'message': f'Unhandled event: {event_type}'}
            
        except Exception as e:
            logger.error(f"Paystack webhook handling error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _handle_subscription_created(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription creation webhook"""
        # Implementation for subscription created
        return {'success': True, 'action': 'subscription_created', 'data': data}
    
    def _handle_subscription_cancelled(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancellation webhook"""
        # Implementation for subscription cancelled
        return {'success': True, 'action': 'subscription_cancelled', 'data': data}
    
    def _handle_payment_failed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment failure webhook"""
        # Implementation for payment failed
        return {'success': True, 'action': 'payment_failed', 'data': data}
    
    def _handle_invoice_updated(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice update webhook"""
        # Implementation for invoice updated
        return {'success': True, 'action': 'invoice_updated', 'data': data}

class StripeGateway(PaymentGateway):
    """Stripe payment gateway implementation"""
    
    def __init__(self):
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    def create_customer(self, email: str, name: str) -> Dict[str, Any]:
        """Create a Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name
            )
            
            return {
                'success': True,
                'customer_id': customer.id,
                'data': customer
            }
            
        except Exception as e:
            logger.error(f"Stripe create customer error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_subscription(self, customer_id: str, plan_id: str, billing_cycle: str) -> Dict[str, Any]:
        """Create a Stripe subscription"""
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': plan_id}],
                payment_behavior='default_incomplete',
                expand=['latest_invoice.payment_intent']
            )
            
            return {
                'success': True,
                'subscription_id': subscription.id,
                'data': subscription,
                'client_secret': subscription.latest_invoice.payment_intent.client_secret
            }
            
        except Exception as e:
            logger.error(f"Stripe create subscription error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel a Stripe subscription"""
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            
            return {
                'success': True,
                'data': subscription
            }
            
        except Exception as e:
            logger.error(f"Stripe cancel subscription error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get Stripe subscription details"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            return {
                'success': True,
                'data': subscription
            }
            
        except Exception as e:
            logger.error(f"Stripe get subscription error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def verify_webhook(self, payload: str, signature: str) -> bool:
        """Verify Stripe webhook signature"""
        try:
            stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return True
            
        except Exception as e:
            logger.error(f"Stripe webhook verification error: {str(e)}")
            return False
    
    def handle_webhook(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        try:
            event_type = event_data.get('type')
            data = event_data.get('data', {}).get('object', {})
            
            if event_type == 'customer.subscription.created':
                return self._handle_subscription_created(data)
            elif event_type == 'customer.subscription.deleted':
                return self._handle_subscription_cancelled(data)
            elif event_type == 'invoice.payment_failed':
                return self._handle_payment_failed(data)
            elif event_type == 'invoice.payment_succeeded':
                return self._handle_payment_succeeded(data)
            
            return {'success': True, 'message': f'Unhandled event: {event_type}'}
            
        except Exception as e:
            logger.error(f"Stripe webhook handling error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _handle_subscription_created(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription creation webhook"""
        return {'success': True, 'action': 'subscription_created', 'data': data}
    
    def _handle_subscription_cancelled(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancellation webhook"""
        return {'success': True, 'action': 'subscription_cancelled', 'data': data}
    
    def _handle_payment_failed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment failure webhook"""
        return {'success': True, 'action': 'payment_failed', 'data': data}
    
    def _handle_payment_succeeded(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment success webhook"""
        return {'success': True, 'action': 'payment_succeeded', 'data': data}

class PaymentGatewayFactory:
    """Factory for creating payment gateway instances"""
    
    @staticmethod
    def create_gateway(provider: str = 'auto', user_location: str = None) -> PaymentGateway:
        """
        Create payment gateway instance
        
        Args:
            provider: 'paystack', 'stripe', or 'auto'
            user_location: User's country code for auto-detection
        """
        if provider == 'auto':
            provider = PaymentGatewayFactory.detect_best_provider(user_location)
        
        if provider == 'paystack':
            return PaystackGateway()
        elif provider == 'stripe':
            return StripeGateway()
        else:
            raise ValueError(f"Unsupported payment provider: {provider}")
    
    @staticmethod
    def detect_best_provider(user_location: str = None) -> str:
        """Detect best payment provider based on user location"""
        # Check if provider is forced in environment
        forced_provider = os.getenv('PAYMENT_PROVIDER', 'auto')
        if forced_provider != 'auto':
            return forced_provider

        # African countries - use Paystack
        african_countries = ['NG', 'GH', 'KE', 'ZA', 'EG', 'MA', 'TN', 'UG', 'TZ', 'RW']

        if user_location and user_location.upper() in african_countries:
            return 'paystack'

        # Default to Stripe for global users
        return 'stripe'
